# Final verification — 30 October 2026

Executed with Python 3.12.14, PySpark 3.5.6, OpenJDK 17.0.20 and SQLite 3.53.1. Windows setup and recovery instructions are provided.

| Verification | Result |
|---|---|
| Automated tests | 55 passed; 0 failures, errors or skips |
| Input preservation | Three input hashes match the original supplied attachments |
| Jharkhand matching | 24 codes in each source; no unmatched baseline records |
| Gold / ML cardinality | 24 unique districts in each output |
| Pension facts | 72 unchanged supplied district/scheme estimates |
| Aggregate controls | Old age 993,567; widow 272,108; disability 31,286 |
| Categories | 8 High, 8 Medium, 8 Low |
| Quality report | 37 PASS, 4 WARN, 0 FAIL |
| SQLite | Integrity OK; seven validation statements return zero violations |
| Repeatability | Gold, ML and sensitivity SHA-256 hashes identical across repeated runs |
| ZIP reproduction | Freshly extracted code executed; output hashes identical |
| Interviewer report | 16 chapters, 18 rendered pages, 8 embedded PNG diagrams; visually reviewed |
| Unexecuted | Native Windows, distributed cluster and production deployment |

## Evidence and interpretation

See outputs/verification_summary.json, outputs/pytest_results.xml, outputs/pytest_execution.log, outputs/zip_reproduction.log, outputs/publication.json and outputs/data_quality_report.md. Four warnings disclose historical/unknown reference periods, supplied estimates, missing eligible denominators and household-universe uncertainty. They are not suppressed test failures.

The final regression injects a failure after a tentative completion PASS but before publication/commit. The failed run retains one FAIL completion record, preserves the previous snapshot and pointer, and releases its lock. Other tests cover pre-commit rollback and post-commit pointer failure.

The clean extraction used the same pinned dependency environment, not a fresh dependency installation. This verifies package independence from the development folder, not compatibility with every machine. Final packaging updates verified sample outputs, documentation and the file manifest; pipeline code/configuration/tests match the executed candidate byte for byte.

Scores range from 14.23242421 to 84.58835663. Godda ranks first under the configured heuristic. Eleven sensitivity scenarios yield 264 comparisons, with maximum rank movement six. These are not official coverage observations or validated policy recommendations.

## Reproduce

```bash
python scripts/verify_environment.py
python scripts/verify_sample.py
python -m src.main --work-dir runtime --logical-date 2026-10-30
python -m src.main --work-dir runtime --logical-date 2026-10-30
python -m pytest -q --junitxml=outputs/pytest_results.xml
python -m src.inspect_db runtime/uddp.sqlite
```

Each run has different IDs, timestamps and audit history. Compare analytical CSV hashes rather than whole database bytes. Retain the rule-derived ML label only as a demonstration; obtain independent historical outcomes before predictive training.
