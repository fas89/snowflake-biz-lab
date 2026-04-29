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
| B1 | `gitlab/path-b-ai-telco-silver-import-demo/variants/B1-ai-reference-external/subscriber360-external/contract.fluid.yaml` | `ai_subscriber360_external_build` | `gitlab/path-a-telco-silver-product-demo/reference-assets/dbt_dv2_subscriber360` | `gitlab/path-b-ai-telco-silver-import-demo/variants/B1-ai-reference-external/subscriber360-external/runtime/generated/airflow/silver_telco_subscriber360_ai_external_v1_dag.py` | `airflow/dags/active/current/silver_telco_subscriber360_ai_external_v1_dag.py` | `silver_telco_subscriber360_ai_external_v1` | `B1-ai-reference-external` | `gitlab/path-b-ai-telco-silver-import-demo/variants/B1-ai-reference-external/subscriber360-external/Jenkinsfile` | `subscriber360_core`, `subscriber_health_scorecard` |
| B2 | `gitlab/path-b-ai-telco-silver-import-demo/variants/B2-ai-generate-in-workspace/subscriber360-generated/contract.fluid.yaml` | `ai_subscriber360_generated_build` | `gitlab/path-b-ai-telco-silver-import-demo/variants/B2-ai-generate-in-workspace/subscriber360-generated/generated/dbt/dbt_dv2_subscriber360` | `gitlab/path-b-ai-telco-silver-import-demo/variants/B2-ai-generate-in-workspace/subscriber360-generated/generated/airflow/silver_telco_subscriber360_ai_generated_v1_dag.py` | `airflow/dags/active/current/silver_telco_subscriber360_ai_generated_v1_dag.py` | `silver_telco_subscriber360_ai_generated_v1` | `B2-ai-generate-in-workspace` | `gitlab/path-b-ai-telco-silver-import-demo/variants/B2-ai-generate-in-workspace/subscriber360-generated/Jenkinsfile` | `subscriber360_core`, `subscriber_health_scorecard` |

## What Should Stay Empty Until You Sync

Before `task jenkins:sync`:

- Jenkins should not show the A1, A2, B1, or B2 job

Before `fluid schedule-sync --scheduler airflow ...`:

- Airflow should not show the A1, A2, B1, or B2 DAG

## dbt Docs Refresh

```bash
task dbt:docs:refresh SCENARIO=A1
task dbt:docs:refresh SCENARIO=A2
task dbt:docs:refresh SCENARIO=B1
task dbt:docs:refresh SCENARIO=B2
```

Then confirm the dbt docs UI at [http://localhost:8086](http://localhost:8086) shows:

- `mart_subscriber360_core`
- `mart_subscriber_health_scorecard`

## End-Of-Scenario Checks

For A1:

- the contract validates and plans cleanly
- the plan review is completed before `apply`
- `apply` finishes with build ID `dv2_subscriber360_reference_build`
- the generated `Jenkinsfile` exists, is committed, and was emitted with `--no-verify-strict-default --publish-stage-default --no-publish-include-env`
- the resulting A1 `Jenkinsfile` has `VERIFY_STRICT=false`, `RUN_STAGE_10_PUBLISH=true`, and a stage-10 `fluid publish` command without the extra `--env` argument
- `task jenkins:sync SCENARIO=A1` succeeds and `A1-external-reference` appears
- `task jenkins:build SCENARIO=A1` succeeds via Jenkins `buildWithParameters`
- the Jenkins console still shows the Snowflake nullability mismatch in `fluid verify`, but non-strict verify keeps it informational for A1
- `fluid schedule-sync --scheduler airflow ...` succeeds against `reference-assets/airflow_subscriber360/dags`
- DAG `telco_subscriber360_reference` appears only after schedule sync
- `task dbt:docs:refresh SCENARIO=A1` succeeds
- the expected exposes appear in DMM after the explicit publish step, and the A1 Jenkins publish stage also completes successfully
- DMM has approved `Access` agreements from `bronze.telco.party_v1`, `bronze.telco.usage_v1`, and `bronze.telco.billing_v1` output ports into the A1 silver product
- DMM Access and lineage views show named Bronze output ports such as `Usage Event Source`, not `Deleted Output Port`
- DMM has no duplicate Bronze SourceSystem nodes for A1 and the A1 silver product has no product-to-product ODPS input ports

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
- DMM has approved `Access` agreements from the Bronze output ports into the A2 silver product
- DMM has no duplicate Bronze SourceSystem nodes for A2 and the A2 silver product has no product-to-product ODPS input ports

For B1:

- `task b1:forge:ai` performs a live Gemini/OpenAI forge and writes `contract.fluid.yaml`
- `runtime/generated/ai-forge/summary.json` and `runtime/generated/ai-forge/raw/.fluid/ai-work-receipt.json` identify the provider/model used for the run
- the live AI-hardened contract validates and plans cleanly
- `fluid generate transformation ... -o runtime/generated/dbt-preview` and `fluid generate schedule ... -o runtime/generated/airflow` both succeed before CI generation
- the plan review is completed before `apply`
- `apply` finishes with build ID `ai_subscriber360_external_build`
- the generated `Jenkinsfile` exists, is committed, and was emitted with `--no-verify-strict-default --publish-stage-default --no-publish-include-env`
- `task jenkins:sync SCENARIO=B1` succeeds and `B1-ai-reference-external` appears
- `task jenkins:build SCENARIO=B1` succeeds via Jenkins `buildWithParameters`
- `fluid schedule-sync --scheduler airflow ...` succeeds against `runtime/generated/airflow`
- DAG `silver_telco_subscriber360_ai_external_v1` appears only after schedule sync
- `task dbt:docs:refresh SCENARIO=B1` succeeds
- the expected exposes appear in DMM after the explicit local `publish` step
- DMM has approved `Access` agreements from the Bronze output ports into the B1 silver product

For B2:

- `task b2:forge:mcp` starts the forge-cli MCP server, reads the seeded Snowflake schema, and writes `contract.fluid.yaml`
- `runtime/generated/mcp-forge/summary.json` and `runtime/generated/mcp-forge/receipt.json` identify the MCP server, Snowflake source, schema, and table count
- the MCP-hardened contract validates and plans cleanly
- generated dbt assets exist under `generated/dbt/dbt_dv2_subscriber360`
- generated Airflow assets exist under `generated/airflow`
- the plan review is completed before `apply`
- `apply` finishes with build ID `ai_subscriber360_generated_build`
- the generated `Jenkinsfile` exists, is committed, and was emitted with `--no-verify-strict-default --publish-stage-default --no-publish-include-env`
- `task jenkins:sync SCENARIO=B2` succeeds and `B2-ai-generate-in-workspace` appears
- `task jenkins:build SCENARIO=B2` succeeds via Jenkins `buildWithParameters`
- `fluid schedule-sync --scheduler airflow ...` succeeds against `generated/airflow`
- DAG `silver_telco_subscriber360_ai_generated_v1` appears only after schedule sync
- `task dbt:docs:refresh SCENARIO=B2` succeeds
- the expected exposes appear in DMM after the explicit local `publish` step
- DMM has approved `Access` agreements from the Bronze output ports into the B2 silver product

For Bronze:

- all three contracts validate and plan cleanly
- all three products appear in DMM
- each Bronze output port links to its per-expose ODCS contract
- no Airflow, dbt, or Jenkins assets are expected
