# Scenario Validation Matrix

Use this after `plan`, `apply`, `task jenkins:sync`, `task jenkins:build`, and the scenario-specific `fluid schedule-sync` command.

## Scenario Matrix

| Scenario | Contract or target | Expected build ID | dbt root | Source Airflow asset | Active Airflow output | Expected DAG ID | Jenkins job | Jenkinsfile path | Expected exposes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Bronze (billing) | `fluid/contracts/telco_seed_billing/contract.fluid.yaml` | Not applicable | Not applicable | Not applicable | Not applicable | Not applicable | Not applicable | Not applicable | `bronze.telco.billing_v1` |
| Bronze (party) | `fluid/contracts/telco_seed_party/contract.fluid.yaml` | Not applicable | Not applicable | Not applicable | Not applicable | Not applicable | Not applicable | Not applicable | `bronze.telco.party_v1` |
| Bronze (usage) | `fluid/contracts/telco_seed_usage/contract.fluid.yaml` | Not applicable | Not applicable | Not applicable | Not applicable | Not applicable | Not applicable | Not applicable | `bronze.telco.usage_v1` |
| A1 | `gitlab/path-a-telco-silver-product-demo/variants/A1-external-reference/contract.fluid.yaml` | `dv2_subscriber360_reference_build` | `gitlab/path-a-telco-silver-product-demo/reference-assets/dbt_dv2_subscriber360` | `gitlab/path-a-telco-silver-product-demo/reference-assets/airflow_subscriber360/dags/telco_subscriber360_pipeline.py` | `airflow/dags/active/current/telco_subscriber360_pipeline.py` | `telco_subscriber360_reference` | `A1-external-reference` | `gitlab/path-a-telco-silver-product-demo/variants/A1-external-reference/Jenkinsfile` | `subscriber360_core`, `subscriber_health_scorecard` |
| A2 | `gitlab/path-a-telco-silver-product-demo/variants/A2-internal-reference/contract.fluid.yaml` | `dv2_subscriber360_internal_build` | `gitlab/path-a-telco-silver-product-demo/variants/A2-internal-reference/dbt_dv2_subscriber360` | `gitlab/path-a-telco-silver-product-demo/variants/A2-internal-reference/airflow_subscriber360/dags/telco_subscriber360_pipeline.py` | `airflow/dags/active/current/telco_subscriber360_pipeline.py` | `telco_subscriber360_internal` | `A2-internal-reference` | `gitlab/path-a-telco-silver-product-demo/variants/A2-internal-reference/Jenkinsfile` | `subscriber360_core`, `subscriber_health_scorecard` |

## What Should Stay Empty Until You Sync

Before `task jenkins:sync`:

- Jenkins should not show the A1 or A2 job

Before `fluid schedule-sync --scheduler airflow ...`:

- Airflow should not show the A1 or A2 DAG

## dbt Docs Refresh

```bash
task dbt:docs:refresh SCENARIO=A1
task dbt:docs:refresh SCENARIO=A2
```

Then confirm the dbt docs UI at [http://localhost:8086](http://localhost:8086) shows:

- `mart_subscriber360_core`
- `mart_subscriber_health_scorecard`

## End-Of-Scenario Checks

For A1:

- the contract validates and plans cleanly
- the plan review is completed before `apply`
- `apply` finishes with build ID `dv2_subscriber360_reference_build`
- the generated `Jenkinsfile` exists, is committed, has `VERIFY_STRICT=false` plus `RUN_STAGE_10_PUBLISH=true`, and removes the unsupported `fluid publish --env ...` flag
- `task jenkins:sync SCENARIO=A1` succeeds and `A1-external-reference` appears
- `task jenkins:build SCENARIO=A1` succeeds via Jenkins `buildWithParameters`
- the Jenkins console still shows the Snowflake nullability mismatch in `fluid verify`, but non-strict verify keeps it informational for A1
- `fluid schedule-sync --scheduler airflow ...` succeeds against `reference-assets/airflow_subscriber360/dags`
- DAG `telco_subscriber360_reference` appears only after schedule sync
- `task dbt:docs:refresh SCENARIO=A1` succeeds
- the expected exposes appear in DMM after the explicit publish step, and the A1 Jenkins publish stage also completes successfully

For A2:

- the contract validates and plans cleanly
- the plan review is completed before `apply`
- `apply` finishes with build ID `dv2_subscriber360_internal_build`
- the generated `Jenkinsfile` exists and is committed
- `task jenkins:sync SCENARIO=A2` succeeds and `A2-internal-reference` appears
- `task jenkins:build SCENARIO=A2` intentionally fails at stage `9 · verify` because `fluid verify ... --strict` treats the Snowflake required-vs-nullable mismatch as a hard gate
- `fluid schedule-sync --scheduler airflow ...` succeeds against `airflow_subscriber360/dags`
- DAG `telco_subscriber360_internal` appears only after schedule sync
- `task dbt:docs:refresh SCENARIO=A2` succeeds
- the expected exposes appear in DMM after the explicit local `publish` step

For Bronze:

- all three contracts validate and plan cleanly
- all three products appear in DMM
- no Airflow, dbt, or Jenkins assets are expected
