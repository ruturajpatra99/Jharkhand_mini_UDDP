# Project analysis and future improvements

## A. Project overview

The Jharkhand Mini-UDDP assessment demonstrates how government departmental aggregates can become a reproducible district analytical dataset. Urban Development and Social Welfare users need a consistent comparison of demographic context, housing vulnerability and pension-related indicators. The output supports an explainable outreach-planning discussion; it cannot establish individual eligibility or prove actual unmet pension need.

This revision uses only the three uploaded CSV  and makes **PySpark 3.5.6 + SQLite** the primary stack. It refactors the earlier implementation's transformation and pension model while preserving its raw-file hashing, canonical district reference, export utilities, CLI conventions, audit tables and transaction/publication boundaries. The earlier deliverable remains separate. This package supersedes its state-only pension NULL outputs with the newly authorized district estimates.

Scope: 24 Census 2011 Jharkhand districts; batch snapshots; public aggregates only; local Spark execution; single SQLite writer; Gold and ML exports; automated testing; analysis, deployment guidance and interviewer documentation. Cloud services, actual individual beneficiaries, real-time integration and a trained predictive model are outside the implemented scope.

## B. Complete requirement analysis

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
| Communication | Interview report, analysis, schema, diagrams and learning walkthrough | reports/, docs/, diagrams/ | Embedded-diagram and rendered-page checks |

A source-level pension model at state/scheme grain is incompatible with claiming observed district counts. The revision resolves the storage requirement by using district/scheme **estimated** facts and a derived state/scheme rollup. It does not reinterpret estimates as observations. Unsupported elderly and eligible-widow fields remain NULL. A trained model, hosted scheduler and extra public sources remain optional and unimplemented.

## C. Dataset analysis

| Source | Exact input filename | Raw rows / columns | Jharkhand rows / keys |
|---|---|---|---|
| Demographics | india-districts-census-2011(3).csv | 640 / 118 | 24 / 24 |
| Housing | District-level households and housing indicators(3).csv | 640 / 156 | 24 / 24 |
| Pension estimates | Jharkhand_District_Estimated_Pension_Beneficiaries_Updated(3).csv | 24 / 8 | 24 / 24 |


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

.



## E. Implementation details

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

## F. Testing and validation

Actual results and package-level evidence are consolidated in `docs/verification.md`, `outputs/verification_summary.json` and pytest's JUnit XML. Tests use the real public aggregate baseline for end-to-end verification and deterministic, clearly separated synthetic defects for failure paths.

Coverage includes strict parsing, aliases, missing/wrong identifiers, housing domains, source scope, duplicate policy, score constants/ties/missingness, input hashes, retry scope, full pipeline reruns, exact 72-value pension preservation, independent score/rate arithmetic, PK/FK/check constraints, bounded collection, SQLite rollback, orchestrated after-load failure, after-commit pointer failure, lock ownership and failed-run audit/alert creation. Freshness cases cover current, stale, future, absent, malformed and timezone-naive timestamps.

Baseline quality has 37 PASS, 4 WARN and 0 FAIL. Warnings disclose historical/unaligned periods, supplied estimates, missing eligible denominators and the household-universe limitation. Gold and ML each contain 24 unique districts. Pension facts have 72 rows and rollups have three. Categories are 8/8/8. There are 264 sensitivity rows: 24 districts across 11 scenarios. Maximum absolute rank movement across tested scenarios is six; excluding pension contributions moves a district by up to four ranks.

Tests and checks validate contracts and arithmetic, not the factual accuracy of the supplied estimates. Native Windows and cloud-server execution are not claimed. The package includes explicit reproduction commands and a read-only inspection utility.

## G. Known limitations

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


## H. Features that would make UDDP more useful

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




