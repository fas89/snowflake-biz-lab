# Snowflake Telco Lab

Snowflake-first telco lab for staged TM Forum SID-style seed data, local platform services, and a FLUID walkthrough that starts empty and becomes visible step by step.

## Start Here

1. [Launchpad Common](docs/launchpad-common.md) for the first-run quickstart, clean-start commands, local logins, and platform bring-up.
2. Pick one track:
   - [Demo Release Launchpad (Mac)](docs/demo-release-launchpad-mac.md)
   - [Demo Release Launchpad (Windows)](docs/demo-release-launchpad-windows.md)
   - [Dev Source Launchpad (Mac)](docs/dev-source-launchpad-mac.md)
   - [Dev Source Launchpad (Windows)](docs/dev-source-launchpad-windows.md)
3. Run Bronze, A1, and A2 from the matching variant playbook:
   - [Variant Playbook (Mac)](docs/variant-playbook-mac.md)
   - [Variant Playbook (Windows)](docs/variant-playbook-windows.md)

## What This Repo Gives You

- Deterministic telco seed data shaped around a practical TM Forum SID-style model
- Dockerized Airflow, dbt-runner, dbt docs UI, Jenkins, and local Entropy / DMM
- FLUID-ready demo workspaces bootstrapped into `./gitlab/` from tracked templates
- Two supported tracks:
  - `demo-release` for the released `data-product-forge` package
  - `dev-source` for an editable sibling `../forge-cli` checkout

## First-Run Expectation

The quickstart now treats "from zero" literally:

- Jenkins starts with no scenario jobs
- Airflow starts with no scenario DAGs
- DMM is ready to log into
- A1 and A2 only appear in Jenkins after `task jenkins:sync`
- A1 and A2 only appear in Airflow after the native `fluid generate artifacts` and `fluid schedule-sync` commands

## Local URLs

- Airflow: [http://localhost:8085](http://localhost:8085)
- dbt docs: [http://localhost:8086](http://localhost:8086)
- Jenkins: [http://localhost:8081](http://localhost:8081)
- Entropy / DMM: [http://localhost:8095](http://localhost:8095)
- MailHog: [http://localhost:8026](http://localhost:8026)

## Repo Map

```text
airflow/              Repo-owned Airflow DAG tree plus the active DAG destination
config/dbt/           Existing dbt profile configuration for Snowflake
dbt/                  Existing staging-only dbt project
deploy/docker/        Docker Compose stacks for Airflow, dbt-runner, Jenkins, and catalogs
docs/                 Quickstarts, playbooks, recovery, and supporting references
fluid/                FLUID contracts, fixtures, prompts, runtime helpers, and reports
fluid/fixtures/workspaces/  Tracked templates copied into ./gitlab/ by task workspaces:bootstrap
gitlab/               Bootstrapped demo workspaces (gitignored)
governance/           Horizon metadata rendering, apply, and verification
runtime/              Ignored local runtime assets like env files and docs output
seed/                 Synthetic telco data generation plus Snowflake loading and verification
```

## Need Help?

- [Launchpad Common](docs/launchpad-common.md)
- [Launchpad Recovery](docs/launchpad-recovery.md)
- [Credentials](docs/credentials.md)
- [Scenario Validation Matrix](docs/scenario-validation-matrix.md)
- [Jenkins SCM Handoff](docs/jenkins-scm-handoff.md)
- [FLUID Gap Register](docs/fluid-gap-register.md)
