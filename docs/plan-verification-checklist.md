# Plan Verification Checklist

Use this checklist after every `fluid plan` run and before every `fluid apply --build`.

The goal is simple: confirm that the plan matches the intended sandbox deployment before anything mutates Snowflake, Jenkins-linked repos, or the local marketplace.

## Files To Open

- `runtime/plan.json`
- `runtime/plan.html`

## Confirm The Target Environment

- Snowflake account matches the sandbox account you intended to use.
- Snowflake database matches the disposable demo database.
- Snowflake schema targets match the expected source or FLUID schemas.
- Snowflake role and warehouse match the intended sandbox role and warehouse.
- No action points at a non-demo database, schema, or catalog target.

## Confirm The Build Scope

- The build ID in your `fluid apply --build <build-id>` command matches the intended `builds[].id` entry in the contract.
- The build step is the expected build for the current variant.
- The build references the expected dbt repository path for that variant.
- The build output names match the expected exposes.
- Generated artifacts land in the expected workspace folders.
- The plan does not contain extra build steps or unexpected destructive actions.

## Confirm Lineage And Upstreams

- The plan references the expected bronze telco source contract as the upstream dependency.
- The intended upstream expose IDs are present for the current silver variant.
- The plan only includes the lineage edges you expected for the variant you are running.
- The plan does not silently swap to a different upstream data product or expose.

## Confirm CI And Publish Intent

- The Jenkins scaffold path is the one you intend to commit and push to GitLab.
- The repo path or script path you plan to hand to Jenkins is correct for the current variant.
- The publish target matches the local marketplace alias you intend to use.
- The plan does not point at a production or shared catalog target.

## Proceed Only If All Of These Are True

- The variant path is correct.
- The Snowflake target is correct.
- The build output is correct.
- The upstream lineage is correct.
- The GitLab/Jenkins handoff path is correct.
- The marketplace target is correct.

If any one of those is wrong, stop and fix the contract, env, or workspace path before running `fluid apply --build`.

After `fluid apply --build`, switch to [Scenario Validation Matrix](scenario-validation-matrix.md) for the end-of-scenario Airflow, dbt, and Jenkins checks.
