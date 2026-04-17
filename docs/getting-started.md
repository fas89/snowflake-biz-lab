# Getting Started

The fastest way into this repo is the [Mac Demo Launchpad](mac-launchpad.md). This page is the short orientation tour.

## What You Need

- Python `3.9+`
- `pip`
- `task` if you want to use the repo helper commands exactly as written
- Docker Desktop for local Airflow, dbt-runner, Jenkins, and Entropy Data CE
- A Snowflake environment when you are ready to load staging data and run live FLUID commands
- A hosted GitLab project or clone path for the two demo workspaces

You do not need Snowflake credentials just to read the docs or inspect the repo layout.

## Two Local Config Files, Two Jobs

1. `.env`
   Put non-secret local settings here, including `FLUID_DEMO_GITLAB_WORKSPACE`.
2. `runtime/generated/fluid.local.env`
   Put Snowflake and DMM secrets here, then load it only before live `fluid apply` or `fluid dmm publish`.

The exact secret model is documented in [Credentials](credentials.md).

## Choose Your FLUID Track

### `demo-release`

Use this for the live story you want to show in front of people.

- installs `data-product-forge==0.7.10` from TestPyPI
- matches the release path you want to demo
- is the default for the Mac runbooks

### `dev-source`

Use this when you want to fix FLUID behavior in `forge-cli` and retest quickly.

- installs from the sibling `../forge-cli` checkout
- should follow remote `main`
- is for engineering iteration, not for the final demo truth

## Copy The Base Environment

```bash
cp .env.example .env
cp .env.catalogs.example .env.catalogs
cp .env.jenkins.example .env.jenkins
```

Then set `FLUID_DEMO_GITLAB_WORKSPACE` in `.env` to the active GitLab working copy you want local Airflow to watch.

Use an absolute macOS path. For example:

```text
FLUID_DEMO_GITLAB_WORKSPACE=/Users/A200004702/gitlab/telco-silver-product-demo
```

## The Recommended Reading Order

1. [Mac Demo Launchpad](mac-launchpad.md)
2. [CLI Version vs `fluidVersion`](fluid-versions.md)
3. [Credentials](credentials.md)
4. [Mac Greenfield Demo](../fluid/demo/mac-greenfield-demo.md)
5. [Mac Existing dbt Demo](../fluid/demo/mac-existing-dbt-demo.md)
6. [FLUID Gap Register](fluid-gap-register.md)

## Local Platform Stack

When you are ready for the local apps:

```bash
task up
task jenkins:up
task catalogs:up
```

The Airflow stack starts without checked-in DAGs. Generated Airflow artifacts become visible through the GitLab workspace bridge.

## Optional Track Checks

If you want to verify the packaged or source runtime before the live demo:

```bash
task fluid:bootstrap:demo
task fluid:check:demo
task fluid:bootstrap:dev
task fluid:check:dev
```

## Need Help?

If something feels off, jump straight to [Troubleshooting](troubleshooting.md). The docs here are intentionally safe to read in order or by topic.
