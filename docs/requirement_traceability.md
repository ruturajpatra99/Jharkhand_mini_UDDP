# Requirement traceability

Original assessment requirements plus revised user requirements. Mandatory versus optional classification and complete eight-column mapping are in the CSV.

| ID | Requirement | Implementation/file | Validation/status |
|---|---|---|---|
| R001 | Read all nine assessment sections | src/extract.py; src/profile_sources.py; config/settings.json | Input hashes; source profile; ingestion tests; Implemented; see verification evidence |
| R002 | Support Urban Development and Social Welfare outreach review | src/extract.py; src/profile_sources.py; config/settings.json | Input hashes; source profile; ingestion tests; Implemented; see verification evidence |
| R003 | Ingest prescribed demographics source and filter Jharkhand | src/extract.py; src/profile_sources.py; config/settings.json | Input hashes; source profile; ingestion tests; Implemented; see verification evidence |
| R004 | Ingest prescribed housing source and filter Jharkhand | src/extract.py; src/profile_sources.py; config/settings.json | Input hashes; source profile; ingestion tests; Implemented; see verification evidence |
| R005 | Ingest prescribed pensions source and filter Jharkhand | src/extract.py; src/profile_sources.py; config/settings.json | Input hashes; source profile; ingestion tests; Implemented; see verification evidence |
| R006 | Use only the three permitted sources | src/extract.py; src/profile_sources.py; config/settings.json | Input hashes; source profile; ingestion tests; Implemented; see verification evidence |
| R007 | Verify live source access and fallback | src/extract.py; src/profile_sources.py; config/settings.json | Input hashes; source profile; ingestion tests; Local sources verified; network downloads are outside revised input scope |
| R008 | Preserve raw unchanged without deleting records | src/extract.py; src/profile_sources.py; config/settings.json | Input hashes; source profile; ingestion tests; Implemented; see verification evidence |
| R009 | Capture source name | src/extract.py; src/profile_sources.py; config/settings.json | Input hashes; source profile; ingestion tests; Implemented; see verification evidence |
| R010 | Capture ingestion timestamp | src/extract.py; src/profile_sources.py; config/settings.json | Input hashes; source profile; ingestion tests; Implemented; see verification evidence |
| R011 | Capture original filename | src/extract.py; src/profile_sources.py; config/settings.json | Input hashes; source profile; ingestion tests; Implemented; see verification evidence |
| R012 | Capture raw row count | src/extract.py; src/profile_sources.py; config/settings.json | Input hashes; source profile; ingestion tests; Implemented; see verification evidence |
| R013 | Standardize district names and handle spelling/case/space differences | src/transform.py | Synthetic defects and source reconciliation tests; Implemented; see verification evidence |
| R014 | Handle district mismatches and unmatched records | src/transform.py | Synthetic defects and source reconciliation tests; Implemented; see verification evidence |
| R015 | Detect and manage duplicates deterministically | src/transform.py | Synthetic defects and source reconciliation tests; Implemented; see verification evidence |
| R016 | Convert numbers and handle blanks, commas, invalid and null values | src/transform.py | Synthetic defects and source reconciliation tests; Implemented; see verification evidence |
| R017 | Create dim_district at one district grain | sql/schema.sql; docs/schema_documentation.md | Schema inspection; constraint tests; foreign_key_check; Implemented; see verification evidence |
| R018 | Create fact_district_demographics at one district grain | sql/schema.sql; docs/schema_documentation.md | Schema inspection; constraint tests; foreign_key_check; Implemented; see verification evidence |
| R019 | Create fact_district_housing at one district grain | sql/schema.sql; docs/schema_documentation.md | Schema inspection; constraint tests; foreign_key_check; Implemented; see verification evidence |
| R020 | Create fact_pension_beneficiaries at one state and scheme grain | sql/schema.sql; docs/schema_documentation.md | Schema inspection; constraint tests; foreign_key_check; Revised grain explicitly authorized by new brief |
| R021 | Create mart_district_pension_outreach at one district grain | sql/schema.sql; docs/schema_documentation.md | Schema inspection; constraint tests; foreign_key_check; Implemented; see verification evidence |
| R022 | Document every table grain and relationships | sql/schema.sql; docs/schema_documentation.md | Schema inspection; constraint tests; foreign_key_check; Implemented; see verification evidence |
| R023 | Gold: District code and standardized name | sql/transformations.sql; src/scoring.py | 24 keys; source-estimate preservation; independent arithmetic; Implemented; see verification evidence |
| R024 | Gold: Total population | sql/transformations.sql; src/scoring.py | 24 keys; source-estimate preservation; independent arithmetic; Implemented; see verification evidence |
| R025 | Gold: Male and female populations | sql/transformations.sql; src/scoring.py | 24 keys; source-estimate preservation; independent arithmetic; Implemented; see verification evidence |
| R026 | Gold: Literate count and literacy indicator | sql/transformations.sql; src/scoring.py | 24 keys; source-estimate preservation; independent arithmetic; Implemented; see verification evidence |
| R027 | Gold: Total workers | sql/transformations.sql; src/scoring.py | 24 keys; source-estimate preservation; independent arithmetic; Implemented; see verification evidence |
| R028 | Gold: SC and ST populations | sql/transformations.sql; src/scoring.py | 24 keys; source-estimate preservation; independent arithmetic; Implemented; see verification evidence |
| R029 | Gold: Total households | sql/transformations.sql; src/scoring.py | 24 keys; source-estimate preservation; independent arithmetic; Implemented; see verification evidence |
| R030 | Gold: Old-age and widow district beneficiary counts | sql/transformations.sql; src/scoring.py | 24 keys; source-estimate preservation; independent arithmetic; Implemented with supplied estimates; observed eligibility coverage unavailable |
| R031 | Gold: Old-age beneficiaries per 1000 population | sql/transformations.sql; src/scoring.py | 24 keys; source-estimate preservation; independent arithmetic; Implemented with supplied estimates; observed eligibility coverage unavailable |
| R032 | Gold: Widow beneficiaries per 1000 population | sql/transformations.sql; src/scoring.py | 24 keys; source-estimate preservation; independent arithmetic; Implemented with supplied estimates; observed eligibility coverage unavailable |
| R033 | Gold: Beneficiaries per 1000 households | sql/transformations.sql; src/scoring.py | 24 keys; source-estimate preservation; independent arithmetic; Implemented with supplied estimates; observed eligibility coverage unavailable |
| R034 | Gold score and High/Medium/Low category | sql/transformations.sql; src/scoring.py | 24 keys; source-estimate preservation; independent arithmetic; Implemented; see verification evidence |
| R035 | Quality: Missing district names or codes | src/transform.py; src/data_quality.py; src/orchestration.py | Quality reports; invalid-input, freshness and failure tests; Implemented; see verification evidence |
| R036 | Quality: Null or invalid required numeric values | src/transform.py; src/data_quality.py; src/orchestration.py | Quality reports; invalid-input, freshness and failure tests; Implemented; see verification evidence |
| R037 | Quality: Nonpositive population | src/transform.py; src/data_quality.py; src/orchestration.py | Quality reports; invalid-input, freshness and failure tests; Implemented; see verification evidence |
| R038 | Quality: Households greater than population | src/transform.py; src/data_quality.py; src/orchestration.py | Quality reports; invalid-input, freshness and failure tests; Implemented; see verification evidence |
| R039 | Quality: Negative pension beneficiaries | src/transform.py; src/data_quality.py; src/orchestration.py | Quality reports; invalid-input, freshness and failure tests; Implemented; see verification evidence |
| R040 | Quality: Raw to transformed reconciliation | src/transform.py; src/data_quality.py; src/orchestration.py | Quality reports; invalid-input, freshness and failure tests; Implemented; see verification evidence |
| R041 | Quality: Ingestion freshness timestamps | src/transform.py; src/data_quality.py; src/orchestration.py | Quality reports; invalid-input, freshness and failure tests; Implemented; see verification evidence |
| R042 | Quarantine or report every bad/unmatched record | src/transform.py; src/data_quality.py; src/orchestration.py | Quality reports; invalid-input, freshness and failure tests; Implemented; see verification evidence |
| R043 | Machine-readable and human-readable quality report | src/transform.py; src/data_quality.py; src/orchestration.py | Quality reports; invalid-input, freshness and failure tests; Implemented; see verification evidence |
| R044 | Create one-row-per-district ML feature table | sql/features.sql; src/features.py; ASSUMPTIONS.md | Feature arithmetic and target consistency; leakage documentation; Implemented; see verification evidence |
| R045 | ML feature: Population per household | sql/features.sql; src/features.py; ASSUMPTIONS.md | Feature arithmetic and target consistency; leakage documentation; Implemented; see verification evidence |
| R046 | ML feature: Female population share | sql/features.sql; src/features.py; ASSUMPTIONS.md | Feature arithmetic and target consistency; leakage documentation; Implemented; see verification evidence |
| R047 | ML feature: Crude literacy share | sql/features.sql; src/features.py; ASSUMPTIONS.md | Feature arithmetic and target consistency; leakage documentation; Implemented; see verification evidence |
| R048 | ML feature: Work participation rate | sql/features.sql; src/features.py; ASSUMPTIONS.md | Feature arithmetic and target consistency; leakage documentation; Implemented; see verification evidence |
| R049 | ML feature: SC population share | sql/features.sql; src/features.py; ASSUMPTIONS.md | Feature arithmetic and target consistency; leakage documentation; Implemented; see verification evidence |
| R050 | ML feature: ST population share | sql/features.sql; src/features.py; ASSUMPTIONS.md | Feature arithmetic and target consistency; leakage documentation; Implemented; see verification evidence |
| R051 | ML pension coverage and household ratio | sql/features.sql; src/features.py; ASSUMPTIONS.md | Feature arithmetic and target consistency; leakage documentation; Implemented with supplied estimates; observed eligibility coverage unavailable |
| R052 | Define high_priority target | sql/features.sql; src/features.py; ASSUMPTIONS.md | Feature arithmetic and target consistency; leakage documentation; Implemented; see verification evidence |
| R053 | Explain leakage prevention and label limitations | sql/features.sql; src/features.py; ASSUMPTIONS.md | Feature arithmetic and target consistency; leakage documentation; Implemented; see verification evidence |
| R054 | Transparent score; no black-box model | src/scoring.py; ASSUMPTIONS.md | Independent calculation; ties/constants/missing-input tests; 11 sensitivity scenarios; Implemented; see verification evidence |
| R055 | Verify elderly share availability | src/scoring.py; ASSUMPTIONS.md | Independent calculation; ties/constants/missing-input tests; 11 sensitivity scenarios; Availability checked; verified 60+ denominator unavailable, field NULL |
| R056 | Feature normalization and missing-value policy | src/scoring.py; ASSUMPTIONS.md | Independent calculation; ties/constants/missing-input tests; 11 sensitivity scenarios; Implemented; see verification evidence |
| R057 | Approximately top33/middle34/bottom33 categories | src/scoring.py; ASSUMPTIONS.md | Independent calculation; ties/constants/missing-input tests; 11 sensitivity scenarios; Implemented; see verification evidence |
| R058 | Sensitivity and reasonableness checks | src/scoring.py; ASSUMPTIONS.md | Independent calculation; ties/constants/missing-input tests; 11 sensitivity scenarios; Implemented; see verification evidence |
| R059 | Permitted orchestration choice | src/orchestration.py; src/load.py; src/main.py | Integration reruns; rollback; pointer failure; lock and retry tests; Implemented; see verification evidence |
| R060 | Operations: Idempotent loads | src/orchestration.py; src/load.py; src/main.py | Integration reruns; rollback; pointer failure; lock and retry tests; Implemented; see verification evidence |
| R061 | Operations: Retry logic | src/orchestration.py; src/load.py; src/main.py | Integration reruns; rollback; pointer failure; lock and retry tests; Implemented; see verification evidence |
| R062 | Operations: Logging | src/orchestration.py; src/load.py; src/main.py | Integration reruns; rollback; pointer failure; lock and retry tests; Implemented; see verification evidence |
| R063 | Operations: Failure alert hook | src/orchestration.py; src/load.py; src/main.py | Integration reruns; rollback; pointer failure; lock and retry tests; Implemented; see verification evidence |
| R064 | Operations: Backfill capability | src/orchestration.py; src/load.py; src/main.py | Integration reruns; rollback; pointer failure; lock and retry tests; Implemented logical-date replay; no invented historical observations |
| R065 | Operations: Configuration outside code | src/orchestration.py; src/load.py; src/main.py | Integration reruns; rollback; pointer failure; lock and retry tests; Implemented; see verification evidence |
| R066 | Operations: Modular functions/tasks | src/orchestration.py; src/load.py; src/main.py | Integration reruns; rollback; pointer failure; lock and retry tests; Implemented; see verification evidence |
| R067 | Transactional rollback and partial-publication handling | src/orchestration.py; src/load.py; src/main.py | Integration reruns; rollback; pointer failure; lock and retry tests; Implemented; see verification evidence |
| R068 | Execution history and audit tables | src/orchestration.py; src/load.py; src/main.py | Integration reruns; rollback; pointer failure; lock and retry tests; Implemented; see verification evidence |
| R069 | Keys, foreign keys and no unintended multiplication | sql/ | Executed Spark queries; SQLite checks and example queries; Implemented; see verification evidence |
| R070 | SQL transformations, validations and final mart scripts | sql/ | Executed Spark queries; SQLite checks and example queries; Implemented; see verification evidence |
| R071 | Complete source code and clean repository | README.md; docs/; reports/; outputs/ | File inventory; rendered Word review; package verification; Implemented; see verification evidence |
| R072 | Architecture diagram | README.md; docs/; reports/; outputs/ | File inventory; rendered Word review; package verification; Implemented; see verification evidence |
| R073 | Data-flow diagram | README.md; docs/; reports/; outputs/ | File inventory; rendered Word review; package verification; Implemented; see verification evidence |
| R074 | Assumptions and district matching rules | README.md; docs/; reports/; outputs/ | File inventory; rendered Word review; package verification; Implemented; see verification evidence |
| R075 | Production scheduling explanation | README.md; docs/; reports/; outputs/ | File inventory; rendered Word review; package verification; Implemented; see verification evidence |
| R076 | Sensitive-data protection extension | README.md; docs/; reports/; outputs/ | File inventory; rendered Word review; package verification; Implemented; see verification evidence |
| R077 | Sample output mart_district_pension_outreach.csv | README.md; docs/; reports/; outputs/ | File inventory; rendered Word review; package verification; Implemented; see verification evidence |
| R078 | Sample output ml_district_features.csv | README.md; docs/; reports/; outputs/ | File inventory; rendered Word review; package verification; Implemented; see verification evidence |
| R079 | Sample output data_quality_report.csv | README.md; docs/; reports/; outputs/ | File inventory; rendered Word review; package verification; Implemented; see verification evidence |
| R080 | Evaluation weights and prioritization | README.md; docs/; reports/; outputs/ | File inventory; rendered Word review; package verification; Implemented; see verification evidence |
| R081 | Python plus SQL, local setup and requirements file | README.md; docs/; reports/; outputs/ | File inventory; rendered Word review; package verification; Implemented; see verification evidence |
| R082 | No citizen/Aadhaar/bank/mobile/ration/individual beneficiary data | README.md; docs/; reports/; outputs/ | File inventory; rendered Word review; package verification; Implemented; see verification evidence |
| R083 | GitHub-ready or ZIP submission | README.md; docs/; reports/; outputs/ | File inventory; rendered Word review; package verification; Implemented; see verification evidence |
| R084 | Compare technology stacks and explain Spark fit | README.md; docs/; reports/; outputs/ | File inventory; rendered Word review; package verification; Primary Spark runtime executed |
| R085 | Prepare interview walkthroughs and at least25 questions | README.md; docs/; reports/; outputs/ | File inventory; rendered Word review; package verification; Implemented; see verification evidence |
| R086 | Optional estimated pension allocation | README.md; docs/; reports/; outputs/ | File inventory; rendered Word review; package verification; Superseded by mandatory supplied-estimate input |
| R087 | Optional additional district pension source | README.md; docs/; reports/; outputs/ | File inventory; rendered Word review; package verification; Not selected; only three authorized inputs |
| R088 | Black-box model, cloud deployment or hosted scheduler | README.md; docs/; reports/; outputs/ | File inventory; rendered Word review; package verification; Optional; not deployed or trained |
| R089 | Mandatory PySpark DataFrames and Spark SQL | src/spark_session.py; src/transform.py; sql/ | Spark 3.5.6 execution; Implemented; execution limits explicitly noted where applicable |
| R090 | Latest exact upload filenames preserved | config/settings.json; data/input | Input manifest hashes; Implemented; execution limits explicitly noted where applicable |
| R091 | Disability pension estimates retained | src/transform.py; sql/transformations.sql | 31,286 total and all source values; Implemented; execution limits explicitly noted where applicable |
| R092 | 72 district/scheme pension facts and 3 estimated state rollups | sql/schema.sql; src/transform.py | Table cardinality and totals; Implemented; execution limits explicitly noted where applicable |
| R093 | Three pension totals reconciled without rescaling | src/data_quality.py | Exact control checks; Implemented; execution limits explicitly noted where applicable |
| R094 | Controlled driver collection and no concurrent SQLite writers | src/load.py; src/orchestration.py | Collection cap; lock test; Implemented; execution limits explicitly noted where applicable |
| R095 | Parameterized batched UPSERT | src/load.py | Existing-key update test; Implemented; execution limits explicitly noted where applicable |
| R096 | All quality results include expected/actual/severity/affected/resolution | src/data_quality.py | Quality contract test; Implemented; execution limits explicitly noted where applicable |
| R097 | Missing/future/stale/naive ingestion timestamps tested | src/data_quality.py; tests/test_quality.py | Parameterized freshness cases; Implemented; execution limits explicitly noted where applicable |
| R098 | Native Windows setup instructions and environment verification | README.md; docs/deployment_guide.md; scripts/verify_environment.py | Linux tested; native Windows not executed; Implemented; execution limits explicitly noted where applicable |
| R099 | pytest plus Spark test utilities | tests/; requirements-dev.txt | JUnit and pytest execution logs; Implemented; execution limits explicitly noted where applicable |
| R100 | Post-commit pointer failure preserves authoritative snapshot | src/orchestration.py; tests/test_pipeline.py | Injected failure test; Implemented; execution limits explicitly noted where applicable |
| R101 | 16-chapter interviewer Word report | reports/Jharkhand_UDDP_Interviewer_Project_Report.docx | Rendered pages and chapter count; Implemented; execution limits explicitly noted where applicable |
| R102 | Eight embedded diagrams and Mermaid sources | scripts/build_report.py; diagrams/; docs/architecture.md | Eight image relationships and render review; Implemented; execution limits explicitly noted where applicable |
| R103 | Comprehensive A-M technical analysis and future feature matrix | PROJECT_ANALYSIS_AND_FUTURE_IMPROVEMENTS.md | Section and requirement review; Implemented; execution limits explicitly noted where applicable |
| R104 | Beginner explanation, 2/5-minute demo and at least25 Q&A | docs/learning_and_demo.md | 35 questions and walkthroughs; Implemented; execution limits explicitly noted where applicable |
| R105 | No-pension sensitivity scenario | src/scoring.py; outputs/score_sensitivity.csv | 264 scenario rows; Implemented; execution limits explicitly noted where applicable |
| R106 | Archive extracted and pipeline rerun | docs/verification.md | Archive reproduction hash comparison; Implemented; execution limits explicitly noted where applicable |
