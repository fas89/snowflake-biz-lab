# Command Reference

This is the short command index that matches the simplified launchpads.

## Most Common Commands

```bash
cd "$LAB_REPO"
task workspaces:bootstrap
task up
task catalogs:up
task catalogs:bootstrap
task preflight
task jenkins:up
task dbt:docs:refresh SCENARIO=A1
task catalogs:reset
task jenkins:sync SCENARIO=A1
task jenkins:build SCENARIO=A1
task jenkins:sync SCENARIO=A2
task jenkins:build SCENARIO=A2
```

## Clean Start

```bash
python3 scripts/reset_demo_state.py --lab-repo "$LAB_REPO" --yes
docker compose -f deploy/docker/docker-compose.yml --env-file .env --profile jenkins down -v --remove-orphans
task catalogs:reset
rm -rf "$LAB_REPO/airflow/dags/active/current"
mkdir -p "$LAB_REPO/airflow/dags/active"
```

## Native Airflow Sync

Run from the scenario directory:

```bash
"$FLUID_CLI" schedule-sync --scheduler airflow --dags-dir ../../reference-assets/airflow_subscriber360/dags --destination "$LAB_REPO/airflow/dags/active/current"
# A2 uses:
# "$FLUID_CLI" schedule-sync --scheduler airflow --dags-dir airflow_subscriber360/dags --destination "$LAB_REPO/airflow/dags/active/current"
```

## Jenkins CI Generation

```bash
"$FLUID_CLI" generate ci contract.fluid.yaml --system jenkins --install-mode "$JENKINS_INSTALL_MODE" --default-publish-target datamesh-manager --out Jenkinsfile
# For A1 only, add:
#   --no-verify-strict-default --publish-stage-default --no-publish-include-env
git status --short -- Jenkinsfile
git add Jenkinsfile
if ! git diff --cached --quiet -- Jenkinsfile; then
  git commit -m "Refresh generated Jenkins pipeline"
else
  echo "Jenkinsfile already committed"
fi
cd "$LAB_REPO"
task jenkins:sync SCENARIO=A1
task jenkins:build SCENARIO=A1
```

## Related Docs

- [Launchpad Common](launchpad-common.md)
- [Variant Playbook (Mac)](variant-playbook-mac.md)
- [Variant Playbook (Windows)](variant-playbook-windows.md)
- [Scenario Validation Matrix](scenario-validation-matrix.md)
