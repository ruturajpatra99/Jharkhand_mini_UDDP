# Architecture and diagram sources

These Mermaid sources accompany the embedded PNGs in the Word report. `scripts/build_report.py` regenerates all eight diagrams from the same documented topology. Spark performs business transformations; the driver writes bounded results to SQLite. Audit and quarantine outputs are first-class run evidence.

## 1. High-level architecture

![System architecture](../diagrams/architecture.png)

```mermaid
flowchart TD
 S[Three uploaded CSVs] --> B[Bronze bytes and manifests]
 B --> P[PySpark DataFrames and SQL]
 P --> V[Validated Silver facts]
 V --> G[Gold score and ML features]
 G --> W[One driver SQLite writer]
 W --> O[Database and versioned CSVs]
 P --> Q[Quality and quarantine]
 Q --> A[Audit and local alerts]
 W --> A
```

## 2. Source-to-target flow

```mermaid
flowchart TD
 D[640 demographic rows] --> DJ[24 Jharkhand districts]
 H[640 housing rows] --> HJ[24 Jharkhand districts]
 P[24 pension estimate rows] --> PS[72 district scheme facts]
 DJ --> J[Validated district join]
 HJ --> J
 PS --> J
 PS --> ST[3 estimated state totals]
 J --> G[24 Gold rows]
 G --> M[24 ML rows]
```

## 3. Medallion responsibilities

```mermaid
flowchart TD
 B[Bronze original bytes] --> S[Silver typed district facts]
 B --> BM[Hashes timestamps and source metadata]
 S --> Q[Matching domains and rejection evidence]
 S --> G[Gold district metrics and ranking]
 G --> M[ML features and rule label]
 G --> E[Versioned exports]
 BM --> L[Run lineage]
 Q --> L
 E --> L
```

## 4. Entity relationships

```mermaid
erDiagram
 dim_district ||--|| fact_district_demographics : identifies
 dim_district ||--|| fact_district_housing : identifies
 dim_district ||--|{ fact_pension_beneficiaries : estimates
 dim_district ||--|| mart_district_pension_outreach : summarizes
 dim_district ||--|| ml_district_features : describes
 etl_run_log ||--|{ source_ingestion_manifest : records
 etl_run_log ||--|{ data_quality_results : checks
 etl_run_log ||--o{ rejected_records : retains
```

## 5. District matching

```mermaid
flowchart TD
 S[Source code and name] --> V[Validate code against canonical set]
 R[Canonical names and aliases] --> V
 V --> N[Validate normalized name]
 N --> K[Check repeated keys]
 K --> A[Left and anti joins]
 A --> Q{Complete expected key sets?}
 Q -->|Yes| J[Inner join to Gold]
 Q -->|No| F[Report unmatched keys and fail]
```

## 6. Quality and quarantine

```mermaid
flowchart TD
 R[Source records] --> V[Schema key numeric and domain checks]
 V -->|Valid| S[Accepted Silver rows]
 V -->|Invalid| Q[Quarantine record and reason]
 S --> C[Reconciliation and completeness gate]
 Q --> C
 C -->|No FAIL| P[Continue to publication]
 C -->|FAIL| A[Failed audit local alert and old snapshot]
```

## 7. Execution and scheduling

```mermaid
flowchart TD
 C[CLI cron or Task Scheduler] --> L[Exclusive lock and run audit]
 L --> T[Extract Spark transform and validate]
 T --> B[Begin SQLite transaction]
 B --> U[UPSERT validate and stage exports]
 U -->|Pass| COM[Commit and successful audit]
 U -->|Failure| R[Rollback and failed audit]
 COM --> P[Update latest success pointer]
 P -->|Failure| REC[Recover via committed audit path]
 R --> A[Local alert and release lock]
 P -->|Success| END[Release lock]
```

## 8. Score flow

```mermaid
flowchart TD
 H[Housing percentages] --> N[Min-max normalization]
 L[Crude literacy] --> I[Inverse min-max]
 P[Estimated old-age and widow rates] --> I
 N --> W[Weighted sum times 100]
 I --> W
 W --> R[Round 8 decimals and rank deterministically]
 R --> C[8 High 8 Medium 8 Low]
 W --> S[Weight perturbations and no-pension scenario]
 C --> T[Rule-derived high_priority label]
```

Run IDs connect metadata, checks and immutable output folders. `etl_run_log` is authoritative if the convenience pointer fails after commit. Source periods are separate from logical execution dates. A model trained on the rule-derived target would not establish independent predictive value.
