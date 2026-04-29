# B1 — AI Forge With External References

The B1 path starts by running `task b1:forge:ai` from the lab repo. That command calls a live LLM provider, writes the generated `subscriber360-external/contract.fluid.yaml`, and preserves the raw forge result under `subscriber360-external/runtime/generated/ai-forge/`. From there the operator regenerates:

- transformation preview assets with `fluid generate transformation`
- Airflow schedule assets with `fluid generate schedule`
- the Jenkins Pipeline-from-SCM file with `fluid generate ci`

The resulting silver contract **references** external dbt assets rather than owning them inside the product folder. Source-of-truth dbt scripts are in `path-a-telco-silver-product-demo/reference-assets/`; B1's generated schedule assets live under `subscriber360-external/runtime/generated/airflow` after the playbook step.

See the variant playbook for the full command sequence.
