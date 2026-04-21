# Internal Reference Variant

This variant packages dbt and Airflow assets inside the data product folder.

- dbt DV2 project: `./dbt_dv2_subscriber360`
- Airflow DAG: `./airflow_subscriber360/dags/telco_subscriber360_pipeline.py`

## Run Order

```bash
fluid validate contract.fluid.yaml
fluid plan contract.fluid.yaml --out runtime/plan.json --html
```

Then verify the plan against [Plan Verification Checklist](../../docs/plan-verification-checklist.md).

If the plan looks correct:

```bash
fluid apply contract.fluid.yaml --build dv2_subscriber360_internal_build --yes
fluid generate ci contract.fluid.yaml --system jenkins --out Jenkinsfile
git add .
git commit -m "Update internal-reference silver variant"
git push
fluid publish contract.fluid.yaml --catalog datamesh-manager
```
