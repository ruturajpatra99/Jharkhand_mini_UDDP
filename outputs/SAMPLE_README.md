# Verified packaged sample

These files are the successful output of a clean ZIP-extraction run. publication.json retains the original immutable run path and hashes. In this packaged sample, analytical CSVs are here and Silver CSVs are in ../data/silver. The database audit retains the original runtime-relative output path for provenance; it is not a link into this flattened sample. Run `python scripts/verify_sample.py` to verify this layout. New executions use their own runtime directory and latest_success pointer.

The SQLite sample holds the latest successful snapshot. JUnit XML records unit/integration/failure/rerun tests; zip_reproduction.log records the extracted-project run. Source data are public aggregates. Earlier final_run/final_rerun logs demonstrate repeatable analytical hashes before the last failure-path fix; the packaged code hash is in publication.json and the clean-extraction log.
