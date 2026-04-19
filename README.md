# Snowflake Telco Lab

Snowflake-first telco lab for staged TM Forum SID-style seed data, Horizon metadata, local platform services, and a full FLUID demo you can run from your Mac.

## Start Here

- Shared setup and reset: [Launchpad Common](docs/launchpad-common.md)
- First-time setup and repo orientation: [Getting Started](docs/getting-started.md)
- Ready-made workspace variants live in `gitlab/telco-silver-product-demo`
- AI workspace variants live in `gitlab/telco-silver-import-demo`
- FLUID work to implement later: [FLUID Gap Register](docs/fluid-gap-register.md)
- Version explanation: [CLI Version vs `fluidVersion`](docs/fluid-versions.md)

After `Launchpad Common`, choose one uninterrupted operator path:

- Mac final demo: [docs/demo-release-launchpad-mac.md](docs/demo-release-launchpad-mac.md)
- Windows final demo: [docs/demo-release-launchpad-windows.md](docs/demo-release-launchpad-windows.md)
- Mac editable source: [docs/dev-source-launchpad-mac.md](docs/dev-source-launchpad-mac.md)
- Windows editable source: [docs/dev-source-launchpad-windows.md](docs/dev-source-launchpad-windows.md)

## What This Repo Gives You

- Deterministic telco seed data shaped around a practical TM Forum SID-style model
- Snowflake landing-table loaders and Horizon metadata scaffolding
- Dockerized Airflow, dbt-runner, Jenkins, and Entropy Data CE platform setup
- FLUID prep for two tracks:
  - `dev-source`: install from the sibling `../forge-cli` checkout for fast upstream fixes
  - `demo-release`: install the latest `data-product-forge` release from TestPyPI
- Friendly Markdown docs written for operators, presenters, and newcomers

## The Main Operator Flow

1. Copy `.env` files and set `FLUID_DEMO_GITLAB_WORKSPACE` to the GitLab working copy you want Airflow to watch.
2. Start local apps from this repo: Airflow, dbt-runner, Jenkins, and Entropy Data CE, then run `task catalogs:bootstrap` so the local Entropy login and `DMM_API_KEY` are ready.
3. Seed Snowflake staging and apply Horizon metadata from this repo.
4. Move into a GitLab-cloned workspace on your Mac and install `data-product-forge`.
5. Run the silver demo variants through `fluid validate`, `fluid plan`, explicit plan verification, `fluid apply --build`, `fluid generate ci`, GitLab push, Jenkins SCM pickup, and `fluid publish`.

The quickest way to run that sequence is:

1. [Launchpad Common](docs/launchpad-common.md)
2. [Demo Release Launchpad (Mac)](docs/demo-release-launchpad-mac.md) or [Demo Release Launchpad (Windows)](docs/demo-release-launchpad-windows.md)

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

- Shared setup and reset: [docs/launchpad-common.md](docs/launchpad-common.md)
- Final demo paths: [docs/demo-release-launchpad-mac.md](docs/demo-release-launchpad-mac.md) and [docs/demo-release-launchpad-windows.md](docs/demo-release-launchpad-windows.md)
- Source-backed paths: [docs/dev-source-launchpad-mac.md](docs/dev-source-launchpad-mac.md) and [docs/dev-source-launchpad-windows.md](docs/dev-source-launchpad-windows.md)
- Exact commands this repo promotes: [docs/command-reference.md](docs/command-reference.md)
- Credentials and runtime secret handling: [docs/credentials.md](docs/credentials.md)
- Common setup issues: [docs/troubleshooting.md](docs/troubleshooting.md)
