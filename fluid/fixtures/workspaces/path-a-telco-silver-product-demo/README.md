# Telco Silver Product Demo

This workspace is the ready-made silver product demo repo.

It contains two contract variants for the same Subscriber 360 / Health product family:

- `variants/external-reference`
- `variants/internal-reference`

Both variants depend on the canonical bronze source contract from the lab repo at `snowflake-biz-lab/fluid/contracts/telco_seed_sources/contract.fluid.yaml`.

## Variant Intent

- **External Reference**
  - references dbt and Airflow assets that are in Git but outside the data product folder
- **Internal Reference**
  - packages dbt and Airflow assets inside the data product folder

## Shared External Assets

- dbt DV2 project: `reference-assets/dbt_dv2_subscriber360`
- Airflow DAGs: `reference-assets/airflow_subscriber360`

## One-Time GitLab Bootstrap

If this workspace is already a GitLab clone, skip this section.

If this workspace is still only a local scaffold on your machine, bootstrap it once before the Jenkins SCM handoff:

```bash
git init -b main
git remote add origin <your-gitlab-url>
git add .
git commit -m "Seed telco silver product demo workspace"
git push -u origin main
```

After that, the normal `generate ci -> commit -> push -> Jenkins scan` flow works as documented.

## Standard Run Order

Run this from the selected variant folder:

1. `fluid validate contract.fluid.yaml`
2. `fluid plan contract.fluid.yaml --out runtime/plan.json --html`
3. verify the plan against [Plan Verification Checklist](docs/plan-verification-checklist.md)
4. `fluid apply contract.fluid.yaml --build <build-id> --yes`
5. `fluid generate ci contract.fluid.yaml --system jenkins --default-publish-target datamesh-manager --out Jenkinsfile`
6. commit and push the repo
7. let Jenkins pick up the generated `Jenkinsfile` from SCM
8. `fluid publish contract.fluid.yaml --catalog datamesh-manager`

For the ready-made variants, use these exact build IDs:

- external variant: `dv2_subscriber360_reference_build`
- internal variant: `dv2_subscriber360_internal_build`

## Jenkins Script Paths

- external variant: `variants/external-reference/Jenkinsfile`
- internal variant: `variants/internal-reference/Jenkinsfile`

See [Jenkins SCM Handoff](docs/jenkins-scm-handoff.md).
