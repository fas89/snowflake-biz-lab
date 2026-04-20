# B2 Golden: AI Forge + Generated Assets

Drop the captured `contract.fluid.yaml` into this folder. The launchpad's B2 demo-mode block copies it verbatim over the contract file inside `$EXISTING_DBT_WORKSPACE/variants/B2-ai-generate-in-workspace/subscriber360-generated/`.

If B2's demo-mode flow also depends on pre-generated `generated/dbt/` and `generated/airflow/` artifacts that `fluid generate transformation`/`fluid generate schedule` would normally build, check those in alongside this contract so the single demo-mode `cp`/`cp -R` step mirrors the full forge + generate output.

Until this folder contains a `contract.fluid.yaml`, the launchpad's B2 demo-mode block will fail with "No such file" — that is intentional so you don't ship a demo without capturing the golden first.

See [../README.md](../README.md) for the full refresh workflow.
