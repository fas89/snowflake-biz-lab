# Snowflake Telco Lab

Snowflake Telco Lab is a telco-only analytics repo built for Snowflake. It prepares local Airflow, dbt, Jenkins, and Data Mesh Manager tooling while keeping Snowflake itself external.

This repo currently focuses on:

- synthetic telco seed generation
- Snowflake landing-table loads via `PUT` and `COPY INTO`
- staging-only dbt models
- Horizon metadata scaffolding for comments, tags, contacts, classification hooks, and DMF hooks
- local Docker services for Airflow, Jenkins, and Entropy Data CE

This repo intentionally does **not** include:

- FLUID contracts, CLIs, or tasks
- multi-business abstractions
- Airflow DAG implementations
- data product publishing automation

## Layout

```text
dbt/                staging-only dbt project
seed/               telco seed generation, load, and verification scripts
governance/         Horizon metadata manifest and SQL rendering/apply/verify
config/dbt/         dbt profiles
airflow/            empty dags/ plus config and plugins placeholders
jenkins/            Jenkins plugins and JCasC
deploy/docker/      main compose stack and catalog stack
docs/               repo notes
runtime/            generated artifacts
```

## Quick Start

1. Copy `.env.example` to `.env`.
2. Copy `.env.catalogs.example` to `.env.catalogs` if you want the local catalog stack.
3. Start the local core services:

```bash
task up
```

4. Generate seed files:

```bash
task seed:generate
```

5. Load seed files into Snowflake:

```bash
task seed:load
```

6. Apply metadata and run dbt staging:

```bash
task metadata:apply
task dbt:run
task dbt:test
```

## Local Endpoints

- Airflow: `http://localhost:${AIRFLOW_WEB_PORT:-8085}`
- Jenkins: `http://localhost:${JENKINS_WEB_PORT:-8081}`
- Entropy Data CE: `http://localhost:${ENTROPY_WEB_PORT:-8095}` when `task catalogs:up` is running
- MailHog: `http://localhost:${MAILHOG_UI_PORT:-8026}` when `task catalogs:up` is running

## Notes

- Seed and metadata commands require Snowflake credentials.
- DMF and classification actions are feature-gated behind `SNOWFLAKE_ENABLE_DMF` and `SNOWFLAKE_ENABLE_CLASSIFICATION`.
- Metadata text is intentionally business-safe and avoids regulated values in Snowflake metadata fields.
