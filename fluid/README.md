# FLUID In This Repo

This folder is the FLUID home for `snowflake-biz-lab`.

## What Is Here

- `contracts/`: prepared Snowflake contracts for the tiny starter path and the telco path
- `demo/`: presenter-friendly runbooks, prompts, and rehearsal checklists
- `fixtures/`: future FLUID fixtures and supporting assets
- `generated/`: generated local outputs such as plans and HTML review artifacts
- `reports/`: saved run summaries and presenter notes
- `scripts/`: small runtime checks for the release and source tracks

## The Two Tracks

### `dev-source`

- uses the sibling `../forge-cli` checkout
- meant for upstream fixes and fast retesting
- should follow `forge-cli` remote `main`

### `demo-release`

- uses TestPyPI `data-product-forge==0.7.10`
- is the required final demo path
- is the track to trust for presenter rehearsal

## Start Here

- [Mac Demo Launchpad](../docs/mac-launchpad.md)
- [Mac Greenfield Demo](demo/mac-greenfield-demo.md)
- [Mac Existing dbt Demo](demo/mac-existing-dbt-demo.md)
- [Rehearsal Checklist](demo/rehearsal-checklist.md)
- [FLUID Gap Register](../docs/fluid-gap-register.md)

## Important Boundaries

- No FLUID coverage harness yet
- No FLUID scenario matrix yet
- No FLUID DMM automation yet
- No dbt changes in this phase
- No `forge-cli` changes are made from this repo
