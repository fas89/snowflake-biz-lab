# Seed Workflow

This repo now generates a broader practical TM Forum SID-style telco dataset rather than a very small starter set.

The synthetic landing model covers:

- party, individual, contact medium, and geographic address
- account and party role
- product offering, subscription, product inventory, service, and resource
- device and SIM inventory
- usage, app events, customer interactions, trouble tickets, and service lifecycle history
- invoices, invoice charges, payments, agreements, and service orders

Core scripts:

- `generate_seed_data.py` writes deterministic telco CSV files into `seed/output/`
- `load_to_snowflake.py` creates the Snowflake landing schemas, stage, file format, and tables, then uses `PUT` and `COPY INTO`
- `verify_seed_data.py` compares manifest counts with the generated files and, when credentials are present, validates row counts in Snowflake

The generated files stay source-shaped on purpose. They are meant to be:

- easy to understand in Snowflake staging
- rich enough for Horizon metadata demos
- rich enough for later FLUID contracts and schema-evolution stories
