"""Spark-native cleaning with explicit mapping, quarantine and scope accounting."""
from __future__ import annotations
import re
from functools import reduce
from pyspark.sql import DataFrame, SparkSession, Window, functions as F, types as T

DEMOGRAPHICS = {'Population': 'population', 'Male': 'male_population',
    'Female': 'female_population', 'Literate': 'literate_population',
    'Workers': 'total_workers', 'SC': 'sc_population', 'ST': 'st_population',
    'Households': 'total_households'}
HOUSING = {'Total Number of Dilapidated': 'dilapidated_pct',
           'Alternative_Source_Open': 'open_defecation_pct'}
PENSIONS = {'Old Age Pension Scheme': 'old_age_estimated_beneficiaries',
    'Widow Pension Scheme': 'widow_estimated_beneficiaries',
    'Divyangjan /Disability Pension Scheme': 'disability_estimated_beneficiaries'}
SOURCE_KEYS = {'demographics': ('State name','District code','District name'),
               'housing': ('State Name','District Code','District Name'),
               'pensions': ('States/UTs','District Code','District')}


def normalize_column(value: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', value.lower()).strip('_')


def normalize_name(column, aliases: dict | None = None):
    value = F.trim(F.regexp_replace(F.lower(column), r'[^a-z0-9]+', ' '))
    if aliases:
        lookup = F.create_map(*[F.lit(x) for pair in aliases.items() for x in pair])
        value = F.coalesce(lookup[value], value)
    return value


def numeric(column, integer: bool = True):
    """Reject malformed commas, exponents, NaN, negatives and fractional counts."""
    text = F.trim(column)
    valid = text.rlike(r'^\+?\d+(\.\d+)?$') | text.rlike(r'^\+?\d{1,3}(,\d{3})+(\.\d+)?$') | text.rlike(r'^\+?\d{1,2}(,\d{2})*,\d{3}(\.\d+)?$')
    number = F.regexp_replace(text, ',', '').cast(T.DecimalType(28, 8))
    valid = valid & number.isNotNull() & (number >= 0)
    if integer:
        valid = valid & F.regexp_replace(text, ',', '').rlike(r'^\+?\d+(\.0+)?$') & (number == F.floor(number)) & (number <= F.lit(9223372036854775807))
    return F.when(valid, number.cast('long' if integer else 'double'))


def read_spark_csv(spark: SparkSession, path: str) -> DataFrame:
    # All strings first: invalid numerics remain available for rejection evidence.
    frame = spark.read.option('header', True).option('inferSchema', False).option('multiLine', True).option('mode','FAILFAST').csv(path)
    names = [normalize_column(c) for c in frame.columns]
    if len(set(names)) != len(names):
        raise ValueError('Columns collide after standardization')
    frame = frame.toDF(*names)
    # One input CSV at a time; this is a logical CSV record number, not a physical line.
    schema = T.StructType(frame.schema.fields + [T.StructField('source_row', T.LongType(), False)])
    return spark.createDataFrame(frame.rdd.zipWithIndex().map(lambda pair: tuple(pair[0]) + (pair[1] + 2,)), schema)


def clean_source(frame: DataFrame, source: str, settings: dict, mapping: dict):
    state, code, name = map(normalize_column, SOURCE_KEYS[source])
    fields = {'demographics': DEMOGRAPHICS, 'housing': HOUSING, 'pensions': PENSIONS}[source]
    required = {state,code,name} | {normalize_column(k) for k in fields}
    if source == 'housing': required |= {'state_code','rural_urban','total_number_of_households'}
    if source == 'pensions': required |= {'category'}
    if missing := required - set(frame.columns):
        raise ValueError(f'{source}: missing required columns {sorted(missing)}')
    original = [c for c in frame.columns if c != 'source_row']
    frame = frame.withColumn('raw_record', F.to_json(F.struct(*[F.col(c) for c in original])))
    frame = frame.withColumn('_state', normalize_name(F.col(state)))
    blank_state = frame.filter(F.col('_state').isNull() | (F.col('_state') == '')).select('source_row','raw_record').withColumn('reason',F.lit('missing_state'))
    outside = frame.filter(F.col('_state').isNotNull() & (F.col('_state') != '') & (F.col('_state') != settings['state'].lower())).count()
    scoped = frame.filter(F.col('_state') == settings['state'].lower())
    # Select independent expressions before aliasing to avoid collisions with source code/name fields.
    selected = scoped.select('source_row','raw_record',F.col(name).alias('raw_name'),
        numeric(F.col(code)).cast('string').alias('district_code'),
        *[numeric(F.col(normalize_column(k)), source != 'housing').alias(v) for k,v in fields.items()],
        *([numeric(F.col('state_code')).cast('string').alias('_state_code'),
           F.lower(F.trim(F.col('rural_urban'))).alias('_geography'),
           numeric(F.col('total_number_of_households'),False).alias('_housing_total')] if source == 'housing' else []),
        *([F.lower(F.trim(F.col('category'))).alias('_category')] if source == 'pensions' else []))
    reference = frame.sparkSession.createDataFrame([(k,v) for k,v in mapping['canonical'].items()],['district_code','canonical_name'])
    selected = selected.join(F.broadcast(reference),'district_code','left')
    issues = [(F.col('district_code').isNull(),'missing_or_invalid_district_code'),
              (F.col('canonical_name').isNull(),'unknown_district_code'),
              (F.col('raw_name').isNull() | (F.trim(F.col('raw_name')) == ''),'missing_district_name'),
              (normalize_name(F.col('raw_name'),mapping['aliases']) != normalize_name(F.col('canonical_name'),mapping['aliases']),'district_code_name_mismatch')]
    issues += [(F.col(v).isNull(), 'invalid_numeric_'+v) for v in fields.values()]
    if source == 'demographics':
        issues += [((F.col('population')<=0) | (F.col('total_households')<=0) | (F.col('total_households')>F.col('population')),'invalid_population_or_households'),
                   (F.col('male_population')+F.col('female_population') != F.col('population'),'population_sex_reconciliation'),
                   (F.col('sc_population')+F.col('st_population') > F.col('population'),'sc_st_exceed_population')]
        issues += [(F.col(v)>F.col('population'),'component_exceeds_population_'+v) for v in ['literate_population','total_workers','sc_population','st_population']]
    elif source == 'housing':
        issues += [(F.coalesce(F.col('_state_code'),F.lit(''))!='20','state_code_name_mismatch'),
                   (F.coalesce(F.col('_geography'),F.lit(''))!='total','unexpected_housing_grain'),
                   (F.coalesce(F.col('_housing_total'),F.lit(-1))!=100,'housing_percentage_semantics_changed')]
        issues += [(F.col(v)>100,'percentage_above_100_'+v) for v in fields.values()]
    else:
        issues += [(F.coalesce(F.col('_category'),F.lit(''))!='district (estimated)','pension_estimate_category_changed')]
    groups = selected.groupBy('district_code').agg(F.countDistinct('raw_record').alias('_variants'))
    selected = selected.join(groups,'district_code','left').withColumn('_ordinal',F.row_number().over(Window.partitionBy('district_code').orderBy('source_row')))
    issues += [(F.col('_variants')>1,'conflicting_duplicate'),((F.col('_variants')==1)&(F.col('_ordinal')>1),'exact_duplicate')]
    selected = selected.withColumn('reason',F.concat_ws(';',*[F.when(condition,F.lit(reason)) for condition,reason in issues])).cache()
    rejected = selected.filter(F.col('reason')!='').select('source_row','raw_record','reason').unionByName(blank_state).withColumn('source_name',F.lit(source)).select('source_name','source_row','reason','raw_record').cache()
    accepted = selected.filter(F.col('reason')=='').select('district_code','raw_name','canonical_name',*fields.values()).cache()
    reconciliation = dict(source_name=source,raw_rows=frame.count(),out_of_scope=outside,
        accepted_source_rows=accepted.count(),rejected_rows=rejected.count(),output_rows=accepted.count()*(3 if source=='pensions' else 1))
    selected.unpersist()
    return accepted,rejected,reconciliation


def transform(spark: SparkSession, manifests: list, settings: dict, mapping: dict):
    clean, rejected, reconciliation = {},[],[]
    for manifest in manifests:
        source=manifest['source_name']
        clean[source],bad,account = clean_source(read_spark_csv(spark,manifest['bronze_path']),source,settings,mapping)
        rejected.append(bad);reconciliation.append(account)
    expected = spark.createDataFrame([(c,) for c in settings['expected_codes']],['district_code'])
    matches=[]
    unmatched=[]
    for source, frame in clean.items():
        keys=frame.select('district_code')
        matches.append(expected.join(keys.withColumn('present',F.lit(True)),'district_code','left').select('district_code',F.lit(source).alias('source_name'),F.when(F.col('present'),F.lit('matched')).otherwise(F.lit('unmatched')).alias('status')))
        unmatched.append(keys.join(expected,'district_code','left_anti').withColumn('source_name',F.lit(source)).withColumn('issue',F.lit('unexpected_key')))
        unmatched.append(expected.join(keys,'district_code','left_anti').withColumn('source_name',F.lit(source)).withColumn('issue',F.lit('missing_valid_key')))
    demo=clean['demographics'];housing=clean['housing'];pension=clean['pensions']
    tables={
      'dim_district':demo.select('district_code',F.col('canonical_name').alias('district_name'),F.lit('20').alias('state_code'),F.lit('Jharkhand').alias('state_name')),
      'fact_district_demographics':demo.select('district_code',F.lit(2011).alias('census_year'),*DEMOGRAPHICS.values()),
      'fact_district_housing':housing.join(demo.select('district_code','total_households'),'district_code','left').select('district_code',F.lit(2011).alias('census_year'),'total_households',F.lit('demographics.Households').alias('household_count_source'),*HOUSING.values()),
      'fact_pension_beneficiaries':pension.select('district_code',F.expr("stack(3, 'old_age', old_age_estimated_beneficiaries, 'widow', widow_estimated_beneficiaries, 'disability', disability_estimated_beneficiaries) as (scheme, estimated_beneficiary_count)")).withColumn('reference_year',F.lit(None).cast('int')).withColumn('is_estimate',F.lit(1)),
      'district_name_mapping':reduce(DataFrame.unionByName,[f.select(F.lit(s).alias('source_name'),'district_code','raw_name',F.col('canonical_name').alias('standardized_name'),F.lit('code_and_validated_name').alias('match_method')) for s,f in clean.items()])}
    tables['pension_state_rollup']=tables['fact_pension_beneficiaries'].groupBy('scheme').agg(F.sum('estimated_beneficiary_count').alias('estimated_beneficiary_count')).withColumn('state_code',F.lit('20')).withColumn('is_estimate',F.lit(1)).select('state_code','scheme','estimated_beneficiary_count','is_estimate')
    return tables,reduce(DataFrame.unionByName,rejected),reconciliation,reduce(DataFrame.unionByName,matches),reduce(DataFrame.unionByName,unmatched)
