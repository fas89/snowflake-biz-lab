# Scenario Validation Matrix

Use this after `plan`, `apply`, `task jenkins:sync`, `task jenkins:build`, and the scenario-specific `fluid schedule-sync` command.

## Scenario Matrix

| Scenario | Contract or target | Acquisition engine | Source (Postgres) | Expected build ID | dbt root | Source Airflow asset | Active Airflow output | Expected DAG ID | Jenkins job | Jenkinsfile path | Expected exposes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Pre-1 | `fluid/contracts/telco_pre1_billing_dlt/contract.fluid.yaml` | `dlt` (acquisition pattern, 0.7.3) | `telco_source.telco.{invoice, invoice_charge}` | `ingest` | Not applicable | Not applicable | Not applicable | Not applicable | `pre1-billing-dlt` | `fluid/contracts/telco_pre1_billing_dlt/Jenkinsfile` | `bronze.telco.billing_v1` (`invoice_source`, `invoice_charge_source`) |
| Pre-2 | `fluid/contracts/telco_pre2_party_airbyte/contract.fluid.yaml` | `airbyte` (acquisition pattern, 0.7.3, embedded deployment) | `telco_source.telco.{party, account, service, subscription, product_offering}` | `ingest` | Not applicable | Not applicable | Not applicable | Not applicable | `pre2-party-airbyte` | `fluid/contracts/telco_pre2_party_airbyte/Jenkinsfile` | `bronze.telco.party_v1` (`party_source`, `account_source`, `service_source`, `subscription_source`, `product_offering_source`) |
| Pre-3 | `fluid/contracts/telco_pre3_usage_meltano/contract.fluid.yaml` | `meltano` (acquisition pattern, 0.7.3, tap-postgres → target-snowflake) | `telco_source.telco.{usage_event, customer_interaction, trouble_ticket}` | `ingest` | Not applicable | Not applicable | Not applicable | Not applicable | `pre3-usage-meltano` | `fluid/contracts/telco_pre3_usage_meltano/Jenkinsfile` | `bronze.telco.usage_v1` (`usage_event_source`, `customer_interaction_source`, `trouble_ticket_source`) |
| A1 | `gitlab/path-a-telco-silver-product-demo/variants/A1-external-reference/contract.fluid.yaml` | `dv2_subscriber360_reference_build` | `gitlab/path-a-telco-silver-product-demo/reference-assets/dbt_dv2_subscriber360` | `gitlab/path-a-telco-silver-product-demo/reference-assets/airflow_subscriber360/dags/telco_subscriber360_pipeline.py` | `airflow/dags/active/current/telco_subscriber360_pipeline.py` | `telco_subscriber360_reference` | `A1-external-reference` | `gitlab/path-a-telco-silver-product-demo/variants/A1-external-reference/Jenkinsfile` | `subscriber360_core`, `subscriber_health_scorecard` |
| A2 | `gitlab/path-a-telco-silver-product-demo/variants/A2-internal-reference/contract.fluid.yaml` | `dv2_subscriber360_internal_build` | `gitlab/path-a-telco-silver-product-demo/variants/A2-internal-reference/dbt_dv2_subscriber360` | `gitlab/path-a-telco-silver-product-demo/variants/A2-internal-reference/airflow_subscriber360/dags/telco_subscriber360_pipeline.py` | `airflow/dags/active/current/telco_subscriber360_pipeline.py` | `telco_subscriber360_internal` | `A2-internal-reference` | `gitlab/path-a-telco-silver-product-demo/variants/A2-internal-reference/Jenkinsfile` | `subscriber360_core`, `subscriber_health_scorecard` |
| B1 | `gitlab/path-b-ai-telco-silver-import-demo/variants/B1-ai-reference-external/subscriber360-external/contract.fluid.yaml` | `ai_subscriber360_external_build` | `gitlab/path-a-telco-silver-product-demo/reference-assets/dbt_dv2_subscriber360` | `gitlab/path-b-ai-telco-silver-import-demo/variants/B1-ai-reference-external/subscriber360-external/runtime/generated/airflow/silver_telco_subscriber360_ai_external_v1_dag.py` | `airflow/dags/active/current/silver_telco_subscriber360_ai_external_v1_dag.py` | `silver_telco_subscriber360_ai_external_v1` | `B1-ai-reference-external` | `gitlab/path-b-ai-telco-silver-import-demo/variants/B1-ai-reference-external/subscriber360-external/Jenkinsfile` | `subscriber360_core`, `subscriber_health_scorecard` |
| B2 | `gitlab/path-b-ai-telco-silver-import-demo/variants/B2-ai-generate-in-workspace/subscriber360-generated/contract.fluid.yaml` | `ai_subscriber360_generated_build` | `gitlab/path-b-ai-telco-silver-import-demo/variants/B2-ai-generate-in-workspace/subscriber360-generated/generated/dbt/dbt_dv2_subscriber360` | `gitlab/path-b-ai-telco-silver-import-demo/variants/B2-ai-generate-in-workspace/subscriber360-generated/generated/airflow/silver_telco_subscriber360_ai_generated_v1_dag.py` | `airflow/dags/active/current/silver_telco_subscriber360_ai_generated_v1_dag.py` | `silver_telco_subscriber360_ai_generated_v1` | `B2-ai-generate-in-workspace` | `gitlab/path-b-ai-telco-silver-import-demo/variants/B2-ai-generate-in-workspace/subscriber360-generated/Jenkinsfile` | `subscriber360_core`, `subscriber_health_scorecard` |

## Pre-Conditions

Before any pre-N or A*/B* job runs:

- Postgres source data must be loaded — run `task seed:postgres:load` to populate `telco_source.telco.*` (24 tables) from the generator's CSVs.

## What Should Stay Empty Until You Sync

Before `task jenkins:sync`:

- Jenkins should not show the pre1, pre2, pre3, A1, A2, B1, or B2 job

Before `fluid schedule-sync --scheduler airflow ...`:

- Airflow should not show the A1, A2, B1, or B2 DAG (pre-* are SDP — no DAG to register)

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
- `task jenkins:build SCENARIO=A2` intentionally fails at stage `9 - verify` because `fluid verify ... --strict` treats the Snowflake required-vs-nullable mismatch as a hard gate
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

For Pre-1 / Pre-2 / Pre-3 (FLUID 0.7.3 acquisition pattern, replaces the legacy passive Bronze):

- the contract validates against schema 0.7.3 and plans cleanly
- the acquisition `builds[0]` block declares the engine (`dlt` / `airbyte` / `meltano`), Postgres source, and capabilities (`full_refresh`, `schema_discovery`)
- `task seed:postgres:load` populated the matching `telco_source.telco.*` tables before the run
- `fluid apply` (stage 7) creates the Snowflake bronze schema + tables AND invokes the matching forge-cli build runner under `schemaEvolution.policy: strict` so the engine cannot mutate the FLUID-applied DDL
- `fluid verify --strict` (stage 9) finds the contract-defined DQ rules satisfied by the rows the engine landed
- `fluid publish` (stage 10) registers the populated product in DMM with `productType: SDP`
- each pre-* output port links to its per-expose ODCS contract
- no Airflow DAG is expected — SDP contracts skip stage 11 (`schedule-sync`)
- the corresponding Jenkins job (`pre1-billing-dlt`, `pre2-party-airbyte`, `pre3-usage-meltano`) appears after `task jenkins:sync SCENARIO=preN` and runs the same 11 stages from `fluid/contracts/telco_pre*_*/Jenkinsfile`
