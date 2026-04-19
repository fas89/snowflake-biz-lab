# Scenario Validation Matrix

Use this after `fluid apply --build`, `fluid generate ci`, and any scenario-specific generation steps.

The goal is simple: confirm that each scenario ends with the expected assets visible in Airflow, dbt, and Jenkins.

## Scenario Matrix

| Scenario | Intent | Contract Or Target | Expected Build ID | dbt Root | Airflow DAG Path | Expected DAG ID | Jenkinsfile Path | Expected Exposes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Bronze | Upstream lineage anchor only | `snowflake-biz-lab/fluid/contracts/telco_seed_sources/contract.fluid.yaml` | Not applicable | Not applicable | Not applicable | Not applicable | Not applicable | Source exposes only |
| A1 | External-reference silver contract | `gitlab/telco-silver-product-demo/variants/external-reference/contract.fluid.yaml` | `dv2_subscriber360_reference_build` | `gitlab/telco-silver-product-demo/reference-assets/dbt_dv2_subscriber360` | `gitlab/telco-silver-product-demo/reference-assets/airflow_subscriber360/dags/telco_subscriber360_pipeline.py` | `telco_subscriber360_reference` | `gitlab/telco-silver-product-demo/variants/external-reference/Jenkinsfile` | `subscriber360_core`, `subscriber_health_scorecard` |
| A2 | Internal-reference silver contract | `gitlab/telco-silver-product-demo/variants/internal-reference/contract.fluid.yaml` | `dv2_subscriber360_internal_build` | `gitlab/telco-silver-product-demo/variants/internal-reference/dbt_dv2_subscriber360` | `gitlab/telco-silver-product-demo/variants/internal-reference/airflow_subscriber360/dags/telco_subscriber360_pipeline.py` | `telco_subscriber360_internal` | `gitlab/telco-silver-product-demo/variants/internal-reference/Jenkinsfile` | `subscriber360_core`, `subscriber_health_scorecard` |
| B1 | AI forge with external references | `gitlab/telco-silver-import-demo/variants/ai-reference-external/subscriber360-external/contract.fluid.yaml` | Inspect generated `contract.fluid.yaml` under `builds:` | `gitlab/telco-silver-product-demo/reference-assets/dbt_dv2_subscriber360` | `gitlab/telco-silver-product-demo/reference-assets/airflow_subscriber360/dags/telco_subscriber360_pipeline.py` | `telco_subscriber360_reference` | `gitlab/telco-silver-import-demo/variants/ai-reference-external/subscriber360-external/Jenkinsfile` | `subscriber360_core`, `subscriber_health_scorecard` |
| B2 | AI forge with generated assets | `gitlab/telco-silver-import-demo/variants/ai-generate-in-workspace/subscriber360-generated/contract.fluid.yaml` | Inspect generated `contract.fluid.yaml` under `builds:` | `gitlab/telco-silver-import-demo/variants/ai-generate-in-workspace/subscriber360-generated/generated/dbt` | `gitlab/telco-silver-import-demo/variants/ai-generate-in-workspace/subscriber360-generated/generated/airflow` | Derived from generated `contract.fluid.yaml` ID with non-alphanumeric characters normalized to `_` | `gitlab/telco-silver-import-demo/variants/ai-generate-in-workspace/subscriber360-generated/Jenkinsfile` | `subscriber360_core`, `subscriber_health_scorecard` |

## dbt UI Refresh

Refresh the local dbt docs site for the scenario you are validating:

```bash
task dbt:docs:refresh SCENARIO=A1
task dbt:docs:refresh SCENARIO=A2
task dbt:docs:refresh SCENARIO=B1
task dbt:docs:refresh SCENARIO=B2
```

Then open:

- dbt docs UI: [http://localhost:8086](http://localhost:8086)

You should see at least:

- `mart_subscriber360_core`
- `mart_subscriber_health_scorecard`

## End-Of-Scenario UI Checks

For silver scenarios, confirm all of these before you call the scenario complete:

- **Airflow**
  - the DAG file exists at the expected path
  - the DAG appears in Airflow UI
  - the DAG ID matches the expected ID or expected generated pattern
- **dbt**
  - the dbt project exists at the expected root
  - `task dbt:docs:refresh SCENARIO=...` succeeds
  - the dbt docs UI shows the expected mart models
- **Jenkins**
  - the `Jenkinsfile` exists at the expected path
  - the repo containing that file has been committed and pushed to GitLab
  - Jenkins discovers the pipeline from SCM
  - the job appears in Jenkins UI under the expected repo/script path

For the bronze anchor scenario, the validation is different:

- contract validates and plans cleanly
- publication works as the lineage anchor
- no Airflow, dbt, or Jenkins assets are expected
