# Project analysis and future improvements

## A. Project overview

The Jharkhand Mini-UDDP assessment demonstrates how government departmental aggregates can become a reproducible district analytical dataset. Urban Development and Social Welfare users need a consistent comparison of demographic context, housing vulnerability and pension-related indicators. The output supports an explainable outreach-planning discussion; it cannot establish individual eligibility or prove actual unmet pension need.

This revision uses only the latest three uploaded CSV snapshots and makes **PySpark 3.5.6 + SQLite** the primary stack. It refactors the earlier implementation's transformation and pension model while preserving its raw-file hashing, canonical district reference, export utilities, CLI conventions, audit tables and transaction/publication boundaries. The earlier deliverable remains separate. This package supersedes its state-only pension NULL outputs with the newly authorized district estimates.



## B. Complete requirement analysis

The official assessment has nine sections: business context, sources, objective, pipeline, score, operations, deliverables, evaluation and submission. Its weights are ETL design 25%, SQL/modeling 20%, data quality 20%, AI readiness 15%, production readiness 10% and documentation 10%. The revised user brief mandates Spark, supplied district estimates, UPSERT, a 16-chapter Word report with eight visuals and this A–M analysis.

`docs/requirement_traceability.csv` contains **106 rows** with requirement ID, description, assessment section, priority, proposed implementation, responsible file, validation and status. `docs/requirement_traceability.md` is the readable companion. It preserves the original 88 requirements and adds 18 explicit revision requirements. Qualified statuses identify unavailable eligibility denominators, native Windows execution limits and optional infrastructure. Mandatory implementation is not conflated with optional deployment.

| Area | Implemented response | Responsible files | Evidence |
|---|---|---|---|
| Inputs and traceability | Three unchanged uploads, hashes, source names, timestamps and counts | extract.py, settings.json | Bronze hashes, manifests, source profiles |
| Spark transformations | Header normalization, state scope, codes/names, type parsing, duplicates and rejects | transform.py | Unit tests, reconciliation and match reports |
| Modeling | Six required business tables, estimated state rollup and audit/mapping tables | schema.sql | SQLite schema inspection, PK/FK/CHECK tests |
| Gold and ML | Spark SQL joins, ratios, five-input score, label | transformations.sql, features.sql, scoring.py | 24 rows each, formula and ranking tests |
| Estimate preservation | No allocation regeneration; all 72 input counts retained | transform.py, data_quality.py | Per-source-value tests; exact three-scheme totals |
| Reliability | Exclusive lock, one writer, UPSERT, rollback, scoped retries, publication authority | orchestration.py, load.py | Reruns, load/pointer failure injection, lock/retry tests |
| Quality | Expected/actual/status/severity/affected/resolution and quarantine | data_quality.py | CSV/JSON/Markdown quality reports |
| Reproducibility | Pinned packages, Windows/Linux commands, CLI and dated run evidence | README, deployment guide | Executed Linux pipeline and tests; Windows limitation disclosed |


A source-level pension model at state/scheme grain is incompatible with claiming observed district counts. The revision resolves the storage requirement by using district/scheme **estimated** facts and a derived state/scheme rollup. It does not reinterpret estimates as observations. Unsupported elderly and eligible-widow fields remain NULL. A trained model, hosted scheduler and extra public sources remain optional and unimplemented.

## C. Dataset analysis

| Source | Exact input filename | Raw rows / columns | Jharkhand rows / keys |
|---|---|---|---|
| Demographics | india-districts-census-2011(3).csv | 640 / 118 | 24 / 24 |
| Housing | District-level households and housing indicators(3).csv | 640 / 156 | 24 / 24 |
| Pension estimates | Jharkhand_District_Estimated_Pension_Beneficiaries_Updated(3).csv | 24 / 8 | 24 / 24 |

The written brief's `(1)` names differ from the newest actual attachment suffixes. The configuration uses the `(3)` filenames and their unchanged bytes. All three current Jharkhand subsets contain the same codes 346–369, exact matching district names, no blank cells and no exact duplicate rows. These findings apply to these snapshots only. Alias handling is implemented and tested with synthetic spelling variants; the baseline did not require guessed fuzzy matching.

`docs/source_column_profile.csv` inventories all **282 original columns** across the files, inferred Jharkhand types, blank/unique counts and a sample. Spark intentionally ingests strings before applying selected target types. The profile's inference is descriptive, not a replacement for explicit transformation schemas. Required selected numerics pass strict conversion/domain checks in the real run. Invalid commas, fractions in count fields, negatives, overflow and NaN are exercised by tests.

The pension header contains `Sl. No.`, `Category`, `States/UTs`, `District`, `District Code`, `Old Age Pension Scheme`, `Widow Pension Scheme`, and `Divyangjan /Disability Pension Scheme`. `Category` is checked as `District (estimated)`. The three totals are 993,567, 272,108 and 31,286, exactly matching supplied controls. The file does not document its allocation method, reference year or error intervals. No assumptions about those missing details are promoted into observed facts.

Housing includes `Total Number of Dilapidated` and `Alternative_Source_Open`, both used as percentage indicators. `Total Number of households` is 100 in all 24 Jharkhand rows. The source contains many additional housing/amenity percentages; their exact names remain in the profile and Bronze, while selected indicators drive the mart. `Rural/Urban=Total` and `State Code=20` are validated to avoid mixing district subgroups or states.

Demographic `Households` supplies the absolute count. The sum of that source field is 7,796,033; total population sums to 32,988,134. The household universe is not independently certified against an official definition. Housing percentages are not multiplied by this count to manufacture housing-condition counts. Crude literacy is Literate/Population; a verified age-seven-plus denominator is absent. `Age_Group_50` does not establish 60-plus share. Female population does not identify eligible widows. These distinctions determine which metrics are computed and which remain NULL.

Raw reconciliation is 640 = 616 out-of-scope + 24 accepted + 0 rejected for demographics and housing; pensions is 24 = 0 + 24 + 0. Pension unpivot creates 72 facts from 24 source rows. The match report has 72 source/district status rows, all matched. No unmatched key is silently removed by the final inner joins.

## D. Problems encountered

The following are actual findings or development issues. Test-injected defects are explicitly distinguished from errors found in supplied real data.

| Actual issue | Root cause and impact | Resolution | Validation | Remaining risk |
|---|---|---|---|---|
| New filenames differ from prose | Repeated uploads acquired `(3)` suffixes; hard-coded `(1)` paths would fail | Configure latest actual filenames and preserve originals | Hashes and manifests against three attachments | Future renames must update config |
| Source headers differ | State/district capitalization and pension column names are not uniform | Central source-key and field dictionaries; normalized headers | Original-column inventory and mapping tests | Undeclared schema changes fail |
| Pension grain changed | Earlier source had one state row; revised source has district estimates | 72 district/scheme facts plus 3 derived state rollups | All source values preserved; exact sums | Estimates remain unverified allocations |
| Housing total equals 100 | Percentage total could be misread as count | Use Census Households count; retain housing percentages | All housing totals checked; provenance stored | Household universes not independently aligned |
| Spark absent initially | Runtime had Java 17 but no pyspark package | Install pinned Spark/py4j in a virtual environment | Actual Spark jobs and version check | Local platform configuration still matters |
| Build isolation dependency fetch blocked | Restricted environment could not obtain an isolated build prerequisite | Build downloaded Spark source with available setuptools/wheel using no-build-isolation | Successful installation and Spark execution | Fresh user environment must have required build tooling |
| pytest collection needed PyArrow | Importing Spark testing utilities initializes pandas-on-Spark dependencies | Pin test-only pandas/NumPy/PyArrow in requirements-dev | Successful pytest collection and suite | Keep test dependency compatibility pinned |
| Early score normalization rounded too soon | Spark SQL decimal division constrained intermediate scale | Cast normalization operands to double and round final score only | Independent Python formula test; final Godda score 84.58835663 | Floating-point comparison uses documented tolerance |
| Resumed environment lost interpreter link | Workspace environment restoration left a broken virtualenv interpreter link | Restore link to the installed runtime interpreter | Spark import and rerun succeeded | Recreate a fresh virtualenv on another machine |
| SQLite cannot accept parallel executor writers safely | Embedded writer locking and transaction scope | One bounded driver collector and one connection with batched UPSERT | Lock, UPSERT, FK, rollback and idempotency tests | Not a high-concurrency production store |
| Rank positions can swap | Unique priority_rank can conflict during incremental per-row rank updates | Refresh Gold/ML derived rows inside the same transaction; UPSERT Silver facts | Rerun and rollback tests | Full derived refresh chosen for 24 rows |
| Quality-report failure after tentative completion | A pending PASS could collide with the FAILED completion audit on its composite key | Replace the tentative completion result before persisting failure | Injected quality-publication failure verifies one FAIL completion, preserved snapshot and released lock | Disk-wide failure may still prevent local audit persistence |
| Filesystem pointer is outside SQLite commit | A post-commit pointer error could mislabel successful data | DB successful-run log is authoritative; preserve committed outputs | Injected after-commit failure test | Recovery may need operator intervention |

No actual district-name conflicts, negative beneficiary values or missing Jharkhand records were found in the supplied inputs. Tests deliberately introduce such conditions, including missing names/codes, wrong state codes, bad numerics, invalid percentages, exact/conflicting duplicates and negative counts. Their purpose is to prove rejection and failure behaviour, not to imply the real sources contained these defects.

Potential production issues such as API outages, distributed data skew, source change-data-capture ordering, concurrent departmental writers and government identity resolution were not encountered in this local run. They belong to the future-risk plan below, not the executed issue log.

## E. Architecture decisions

**Why Spark:** required by the revised brief, and useful for demonstrating reusable expression-based cleansing, joins, aggregations and windows. Local[2] is an execution mode, not evidence of cluster scalability. For 24 output districts the JVM startup is overhead; a simpler Python/SQLite solution could be faster locally but would not satisfy the revised stack requirement.

**Why SQLite:** it minimizes infrastructure while retaining relational constraints and transactional SQL. The driver only collects bounded, validated district tables. A JDBC connector was unnecessary; no claim of direct Spark-to-SQLite writing is made. PostgreSQL or a warehouse is a better serving layer once concurrent readers/writers, large history or departmental SLAs become material.

**Why medallion layers:** Bronze preserves evidence, Silver establishes consistent meaning and keys, Gold exposes question-specific metrics. Run-specific exports and input/code/config hashes connect these layers. Quarantine is a side output with records and reasons, not a silent filter.

**Why keys plus names:** canonical Census district codes provide stable joins for these source years. A second name check catches wrongly assigned codes. Controlled aliases are explainable; fuzzy matching was rejected because an uncertain match should not become a silent administrative fact.

**Why these weights:** 80% combines housing and literacy need proxies; 20% uses low estimated pension rates to satisfy the revised analytical intent without allowing them to dominate. Weights are policy choices, not statistical discoveries. Equal per-person estimated rates could make pension inputs uninformative; constant inputs receive zero. In this file, widow estimates vary only from roughly 8.0704 to 8.4928 per 1,000 population, so min-max normalization amplifies a narrow range. This is a material limitation, not a calibrated effect size. The no-pension sensitivity scenario helps expose it.

**Why no trained model:** the target is derived from the same score inputs, and there are only 24 records. Training on it would mainly learn the deterministic rule. A proper outcome could be later independently audited outreach uptake with features fixed before intervention. Current outputs are feature contracts and illustrative labels, not predictive evidence.

## F. Implementation details

| Module/file | Responsibility | Key functions or operations |
|---|---|---|
| extract.py | Validate CSV shape, preserve bytes, hash and manifest | read_csv, digest, extract, utcnow |
| spark_session.py | Spark lifecycle and local settings | create_spark |
| transform.py | Spark string ingestion, typing, matching and Silver facts | read_spark_csv, numeric, normalize_name, clean_source, transform |
| data_quality.py | Quality contracts and blocking gates | result, enforce, ingestion_freshness, preflight, gold_checks |
| scoring.py | Normalize, score, rank, perturb weights | normalize, score, rank_scores, sensitivity |
| features.py | Execute versioned feature SQL | build_features |
| load.py | Parameterized single-writer database and exports | connect, upsert, bounded_rows, load_snapshot, execute_script |
| orchestration.py | Lock, retry, audit, transaction and publication | run, retry, event, alert, write_quality |
| main.py | CLI, environment overrides and date replay | main |
| profile_sources.py | Complete source inventory | profile |
| inspect_db.py | Read-only demonstration | main |
| transformations.sql | CTE pension pivot and district joins | Spark SQL |
| features.sql | Ratios and deterministic target | Spark SQL |
| schema.sql | All table/constraint declarations | SQLite DDL |
| validations.sql, analytics.sql | Independent checks and query examples | SQLite SQL |

Each source is filtered case-insensitively through its declared state field. Missing state values are rejected rather than counted outside scope. Valid non-Jharkhand records are explicitly counted outside scope. Numeric parsing accepts valid Indian/Western comma grouping but rejects malformed grouping, exponent text, negative counts, count fractions and overflow. A tiny nonzero fractional suffix cannot round into an accepted integer count.

Exact duplicates retain the earliest logical CSV record and report later copies; conflicts quarantine all versions. `source_row` counts logical CSV records including the header offset, not physical lines in a quoted multiline file. Invalid rows retain JSON of normalized source columns; Bronze retains the exact original header/bytes.

Before the load, Spark outputs pass required keys, matching and cardinality checks. Driver collection is bounded to 1,000 rows per table; SQLite batches use 100 rows. The loader validates column sets against the actual schema. SQL values are parameterized. `execute_script` uses individual execute calls so it does not implicitly pre-commit an active transaction.

Outputs are staged in a run-specific folder before database commit. The transaction records business rows, quality checks and success status together. The latest-success pointer is written afterward. Failed/candidate folders must not be consumed without a successful authoritative audit. Extraction I/O retry uses bounded exponential delay; validation failures are not retried. Backfill accepts at most 32 dates and reuses explicitly selected input snapshots.

## G. Testing and validation

Actual results and package-level evidence are consolidated in `docs/verification.md`, `outputs/verification_summary.json` and pytest's JUnit XML. Tests use the real public aggregate baseline for end-to-end verification and deterministic, clearly separated synthetic defects for failure paths.

Coverage includes strict parsing, aliases, missing/wrong identifiers, housing domains, source scope, duplicate policy, score constants/ties/missingness, input hashes, retry scope, full pipeline reruns, exact 72-value pension preservation, independent score/rate arithmetic, PK/FK/check constraints, bounded collection, SQLite rollback, orchestrated after-load failure, after-commit pointer failure, lock ownership and failed-run audit/alert creation. Freshness cases cover current, stale, future, absent, malformed and timezone-naive timestamps.

Baseline quality has 37 PASS, 4 WARN and 0 FAIL. Warnings disclose historical/unaligned periods, supplied estimates, missing eligible denominators and the household-universe limitation. Gold and ML each contain 24 unique districts. Pension facts have 72 rows and rollups have three. Categories are 8/8/8. There are 264 sensitivity rows: 24 districts across 11 scenarios. Maximum absolute rank movement across tested scenarios is six; excluding pension contributions moves a district by up to four ranks.

Tests and checks validate contracts and arithmetic, not the factual accuracy of the supplied estimates. Native Windows and cloud-server execution are not claimed. The package includes explicit reproduction commands and a read-only inspection utility.

## H. Known limitations

- District pension values are estimates, with no documented allocation method, reference period or uncertainty intervals in the three primary files.
- Census values are historical and use Census district identities. Current administrative boundaries and LGD codes may need crosswalks.
- Population/household-normalized entries do not measure eligible-person coverage. Scheme overlap prevents unique-person/household inference.
- The demographic household count and housing percentage universe have not been independently reconciled.
- Min-max scaling is relative to this cohort and can magnify small estimated-rate differences. Weights are not officially validated.
- Backfill is logical execution replay, not a historical observation store. Business keys represent the latest snapshot.
- The driver boundary and SQLite store intentionally constrain output size and concurrent writes. No distributed performance benchmark is claimed.
- A local lock can remain after a hard process crash; recovery requires verifying process state. No automatic unsafe lock deletion is implemented.
- No live APIs, CDC, streaming or automatic external alerts are implemented. Scheduling guidance is provided, not a deployed production service.
- The ML label is rule-derived; it has no independently established predictive meaning.

## I. Future implementations

Prioritize better source meaning before more infrastructure. First obtain approved current district pension observations, reference periods, documented household definitions and eligible populations. Introduce source contracts with owner, schema, grain, refresh schedule, coding system, privacy classification and permitted use. Maintain immutable snapshots and code/config hashes during every migration.

Next add API/file adapters with schema-version detection, authenticated secret handling, rate limiting and retrieval checkpoints. Incremental loading requires stable source keys, modification times/tombstones and explicit late-arrival rules. CDC is appropriate only when source transaction semantics, deletes and ordering are available; it is not equivalent to repeatedly downloading snapshots.

For larger workloads, store Bronze/Silver in governed object storage using partitioned Parquet and a transaction-capable table format where justified. Replace driver collection with partitioned staging. Bulk-load PostgreSQL or a warehouse, validate the staged batch and merge under controlled transaction semantics. Add Airflow/another orchestrator when dependencies, SLAs and recovery need it, not merely to add a tool name.

Introduce a metadata catalog, column lineage, schema-change alerts, row-volume and distribution monitoring, and source freshness dashboards. Baseline statistical anomaly alerts should be reviewed alongside known policy/boundary changes. New ML development needs independent labels, temporal holdouts, train-only preprocessing, drift monitoring and intervention-aware evaluation.

For sensitive integrations, separate identity linkage from analytical marts; apply least privilege, encryption, managed keys, audit trails, retention rules and small-cell protection. A hash of a predictable identifier alone is not anonymization. Real government data requires explicit authorization and governance before collection.

## J. Features that would make UDDP more useful

| Feature | Business benefit | Technical requirements | Complexity | Priority | Dependencies and data needed |
|---|---|---|---|---|---|
| Power BI dashboard | Explain district profiles and score contributions | Read-only semantic model, refresh, labels | Low/medium | Near term | Current mart; users understand estimate status |
| District comparison | Compare demographics and vulnerability transparently | Consistent units, cohort filters | Low | Near term | Existing mart and dictionary |
| Data freshness dashboard | Expose stale departmental submissions | Ingestion and observation timestamps separately | Low | Near term | Run logs plus source reference dates |
| Missing-data alerts | Trigger correction before publication | Quality event routing and owner directory | Medium | Near term | Approved alert channel and ownership |
| Department ingestion monitoring | Track SLAs and failures across systems | Contract registry, metrics, orchestrator | Medium | Near term | Department IDs and refresh commitments |
| What-if weight simulations | Reveal ranking sensitivity to policy choices | Versioned parameter UI and scenario store | Medium | Near term | Existing normalized features; approved interpretation |
| Outreach heatmaps | Communicate geography and clustering | Licensed boundary geometries and code crosswalk | Medium | Later | Verified current/Census boundaries; not provided now |
| Scheme trends | Distinguish change from snapshot differences | Period-keyed facts and denominator alignment | Medium/high | After source upgrade | Multiple comparable observed periods |
| Scheme performance tracking | Monitor enrollment/outreach effectiveness | Independent outcome definitions and quality controls | High | After source upgrade | Observed uptake, eligible populations, dates |
| Priority recommendations | Help allocate outreach resources with explanations | Policy constraints, impact review, feedback | High | After validation | Current verified need and resource/outcome data |
| Explainable ML support | Predict an independently measured future outcome | Historical features, leakage checks, temporal evaluation | High | Long term | Sufficient independent labels; current rule label inadequate |

No dashboard, boundary map or ML model is claimed to have been built in this revision. These are ranked proposals with explicit prerequisites.

## K. Scaling to 23 departments

Use a configuration-driven framework with one adapter per access pattern (file/API/database), not one bespoke pipeline per district. Each department owns a versioned contract. Ingestion creates immutable source batches with checksums and logical/observation time. Validation maps fields into canonical domains while preserving source identifiers and lineage. Cross-department linkage must account for geography versions, schemes, units and time before joining.

Illustrative future mapping, not an additional source used in the assessment:

```json
{
  "department": "example_agriculture",
  "contract_version": "1.0",
  "source_grain": "district_scheme_period",
  "geography_system": "verified_lgd",
  "columns": {
    "DistrictIdentifier": "district_code",
    "Programme": "scheme_code",
    "ReferenceMonth": "observation_period",
    "AggregateCount": "beneficiary_count"
  },
  "required": ["district_code", "scheme_code", "observation_period", "beneficiary_count"],
  "privacy_classification": "approved_aggregate",
  "load_key": ["district_code", "scheme_code", "observation_period"],
  "quality": {"beneficiary_count_min": 0, "unknown_district": "quarantine"}
}
```

Spark can broadcast small reference dimensions, prune unused columns early, partition large data by source/period and avoid global windows until aggregation reaches district grain. Measure skew and shuffle rather than assuming more machines solve poor keys. Replace SQLite with a transactional staging/merge target once departmental concurrency or history requires it. Establish source ownership, run lineage and observability across all 23 feeds. Citizen-level matching, if authorized in a separate future project, belongs in a protected identity domain and should expose minimal pseudonymous linkage to analytics.

## L. Deployment roadmap

| Horizon | Deliverables | Exit evidence |
|---|---|---|
| Short term: assessment/local pilot | Reproduce pinned environment, review assumptions, demonstrate current pipeline, assign source owners | Tests pass, hashes match, stakeholder understands estimate limitations |
| Next 2–6 weeks, subject to access | Verified current observations/periods, household definitions, eligible denominators, contract registry, read-only dashboard | Data owner sign-off, reconciled definitions and reviewed metric interpretation |
| Medium term: 1–3 months | API/file adapters, scheduled orchestration, PostgreSQL staging/merge, monitoring and backups | Recovery drill, SLA evidence, incremental correctness tests |
| Longer term: phased program | Governed lake/catalog, 23-department contracts, authorized privacy-preserving linkage and independent outcome analysis | Access approval, lineage coverage, security review and measured outcome validation |

These time windows are planning estimates, not delivery commitments. Government access, procurement and data quality can dominate elapsed time. The two-day assessment prioritizes a functional vertical slice first: input contract → one district join → quality gate → SQLite output, followed by failure tests, scoring/ML interpretation and documentation.

## M. Final recommendations

The highest-value next investment is verified current data with documented grain and observation periods. Without that, more complex scoring or machine learning can create confidence without stronger evidence. Keep supplied estimates visibly labelled and retain the no-pension scenario when presenting rankings.

For the assessment, demonstrate the actual Spark code, source-value preservation, complete district matching and rollback/idempotency evidence. Explain why a single SQLite writer is appropriate for the small output, how the transaction boundary works, and what must change at scale. Use the Word report for technical review and the separate learning guide for rehearsal.

For a real UDDP rollout, add source governance and monitoring, then a concurrent database and orchestration, then independent outcomes and responsible predictive analysis. Preserve the engineering principle established here: every published metric must have a traceable source, defined unit, valid grain and explicit interpretation limit.

## Excel Dashboard and District Priority Analytics

A native Excel dashboard after the three CSV outputs. The extension uses openpyxl, preserving the existing Spark transformations, SQLite schema and priority methodology. `src/excel_dashboard.py` validates the actual mart/ML/matching schemas, writes six worksheets, creates formula KPI cards and native charts, and supports standalone generation with no SparkSession. The orchestrator generates its immutable candidate before commit and atomically publishes a latest workbook after commit. Failure/transaction boundaries and recovery are documented in docs/excel_dashboard.md.

High districts are selected from the existing category and sorted using the existing score/rank. No independent thresholds or allocations are added. FormulaRule conditional formatting detects the category column dynamically and colors the entire data row only on the mart and ML sheets. Missing ML categories are derived only in Excel through verified district keys; unmatched keys remain Unknown. District matching is measured at both district and source-record grains with explicit denominators.

The workbook provides category distribution, top-ten ranking, estimated scheme comparisons, population/score comparison, matching status, outreach rates, filters and two-district dropdowns. It is a generated analytical snapshot. openpyxl does not evaluate formulas; Excel recalculates on opening. No slicers, pivot charts or native Excel desktop execution are claimed. Formula/cache and layout verification are recorded with extension-specific evidence rather than inventing Excel test results.

A future Power BI model could use the same validated data for cross-filtering, maps and refresh governance. Maps require verified district boundaries and crosswalks; trends need dated observations. Current counts, allocation provenance and eligible denominators remain the highest-value data improvements before operational scheme monitoring. The extension addresses presentation accessibility, not source uncertainty.
