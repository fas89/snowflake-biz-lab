# Snowflake Telco Lab

Snowflake-first telco lab for staged TM Forum SID-style seed data, Horizon metadata, local platform services, and a full FLUID demo you can run from your Mac.

## Start Here

- Running the whole demo from your Mac: [Mac Demo Launchpad](docs/mac-launchpad.md)
- First-time setup and repo orientation: [Getting Started](docs/getting-started.md)
- Primary end-to-end demo: [Mac Greenfield Demo](fluid/demo/mac-greenfield-demo.md)
- Secondary existing-dbt variation: [Mac Existing dbt Demo](fluid/demo/mac-existing-dbt-demo.md)
- FLUID work to implement later: [FLUID Gap Register](docs/fluid-gap-register.md)
- Version explanation: [CLI Version vs `fluidVersion`](docs/fluid-versions.md)

## What This Repo Gives You

- Deterministic telco seed data shaped around a practical TM Forum SID-style model
- Snowflake landing-table loaders and Horizon metadata scaffolding
- Dockerized Airflow, dbt-runner, Jenkins, and Entropy Data CE platform setup
- FLUID prep for two tracks:
  - `dev-source`: install from the sibling `../forge-cli` checkout for fast upstream fixes
  - `demo-release`: install the pinned TestPyPI release `data-product-forge==0.7.10`
- Friendly Markdown docs written for operators, presenters, and newcomers

## The Main Operator Flow

1. Copy `.env` files and set `FLUID_DEMO_GITLAB_WORKSPACE` to the GitLab working copy you want Airflow to watch.
2. Start local apps from this repo: Airflow, dbt-runner, Jenkins, and Entropy Data CE.
3. Seed Snowflake staging and apply Horizon metadata from this repo.
4. Move into a GitLab-cloned workspace on your Mac and install `data-product-forge`.
5. Run `fluid init`, `fluid forge`, `fluid generate schedule`, `fluid generate ci`, `fluid validate`, `fluid plan`, `fluid apply`, `fluid generate standard`, and `fluid dmm publish`.

The quick operator page for that sequence is [Mac Demo Launchpad](docs/mac-launchpad.md).

## Local URLs

- Airflow: [http://localhost:8085](http://localhost:8085)
- Jenkins: [http://localhost:8081](http://localhost:8081)
- Entropy / DMM: [http://localhost:8095](http://localhost:8095)
- MailHog: [http://localhost:8026](http://localhost:8026)

## Repo Map

```text
airflow/              Airflow scaffold plus a workspace-mounted DAG bridge
config/dbt/           Existing dbt profile configuration for Snowflake
dbt/                  Existing staging-only dbt project, unchanged in this phase
deploy/docker/        Docker Compose stacks for Airflow, dbt-runner, Jenkins, and catalogs
docs/                 Operator docs, setup guides, launchpad, and troubleshooting
fluid/                FLUID contracts, demo runbooks, prompts, runtime helpers, and reports
governance/           Horizon metadata manifest, SQL rendering, verification, and DMM mapping
runtime/              Ignored local runtime assets like env files and demo wheels
seed/                 Synthetic telco data generation plus Snowflake loading and verification
```

## Important Boundaries

- No FLUID coverage harness yet
- No FLUID scenario matrix yet
- No checked-in Airflow DAG Python files yet
- No dbt project changes in this phase
- No `forge-cli` changes are made in this repo; gaps are documented instead

## Need Help?

- Operator-first path: [docs/mac-launchpad.md](docs/mac-launchpad.md)
- Exact commands this repo promotes: [docs/command-reference.md](docs/command-reference.md)
- Credentials and runtime secret handling: [docs/credentials.md](docs/credentials.md)
- Common setup issues: [docs/troubleshooting.md](docs/troubleshooting.md)
