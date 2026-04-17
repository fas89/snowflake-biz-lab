# Seed Workflow

- `generate_seed_data.py` writes deterministic telco CSV files into `seed/output/`.
- `load_to_snowflake.py` creates the Snowflake landing schemas, stage, file format, and tables, then uses `PUT` and `COPY INTO`.
- `verify_seed_data.py` compares manifest counts with the generated files and, when credentials are present, validates row counts in Snowflake.
