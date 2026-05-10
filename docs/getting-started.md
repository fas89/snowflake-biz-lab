# Getting Started

The recommended reading order is now intentionally short:

1. [Launchpad Common](launchpad-common.md)
2. Pick one track:
   - [Demo Release Launchpad (Mac)](demo-release-launchpad-mac.md)
   - [Demo Release Launchpad (Windows)](demo-release-launchpad-windows.md)
   - [Dev Source Launchpad (Mac)](dev-source-launchpad-mac.md)
   - [Dev Source Launchpad (Windows)](dev-source-launchpad-windows.md)
3. Run the scenarios from the matching variant playbook:
   - **Pre-1 / Pre-2 / Pre-3** — bronze acquisition (dlt / PyAirbyte / Meltano → Snowflake)
   - **A1 / A2** — silver via curated dbt (external-reference / internal-reference)
   - **B1 / B2** — silver via AI-forged dbt (live AI reference / MCP-discovered generation)
   - **C1** — gold composition (CDP from B1+B2 silver products)

## What You Need

- Python `3.9+`
- `pip`
- `task`
- Docker Desktop
- a Snowflake environment when you are ready for the live seed and FLUID steps

## What The Quickstart Assumes

- demo workspaces live in `./gitlab/` and are bootstrapped from `fluid/fixtures/workspaces/`
- Jenkins starts empty
- Airflow starts empty
- DMM login is visible in the quickstart instead of hidden in a separate credential hunt

For the full first-run path, stop here and continue to [Launchpad Common](launchpad-common.md).
