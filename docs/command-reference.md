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
task b1:forge:ai -- --provider gemini --model gemini-2.5-flash
task b2:forge:mcp
task dbt:docs:refresh SCENARIO=A1
task catalogs:reset
task jenkins:sync SCENARIO=A1
task jenkins:build SCENARIO=A1
task jenkins:sync SCENARIO=A2
task jenkins:build SCENARIO=A2
task jenkins:sync SCENARIO=B1
task jenkins:build SCENARIO=B1
task jenkins:sync SCENARIO=B2
task jenkins:build SCENARIO=B2
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
# B1 uses:
# "$FLUID_CLI" schedule-sync --scheduler airflow --dags-dir runtime/generated/airflow --destination "$LAB_REPO/airflow/dags/active/current"
# B2 uses:
# "$FLUID_CLI" schedule-sync --scheduler airflow --dags-dir generated/airflow --destination "$LAB_REPO/airflow/dags/active/current"
```

## Jenkins CI Generation

```bash
"$FLUID_CLI" generate ci contract.fluid.yaml --system jenkins --install-mode "$JENKINS_INSTALL_MODE" --default-publish-target datamesh-manager --out Jenkinsfile
# For A1 and B1, add:
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
# For B1, run `task b1:forge:ai` first, then run the same generate command from:
# "$EXISTING_DBT_WORKSPACE/variants/B1-ai-reference-external/subscriber360-external"
# then use: task jenkins:sync SCENARIO=B1 && task jenkins:build SCENARIO=B1
# For B2, run `task b2:forge:mcp` first. That task writes the generated
# Jenkinsfile under:
# "$EXISTING_DBT_WORKSPACE/variants/B2-ai-generate-in-workspace/subscriber360-generated"
# then use: task jenkins:sync SCENARIO=B2 && task jenkins:build SCENARIO=B2
```

In the demo-release track, `task jenkins:sync` and `task jenkins:build` read `runtime/generated/demo-release.env`, so Jenkins uses the same resolved TestPyPI package as your local `fluid` command without extra `--param` flags.

## Related Docs

- [Launchpad Common](launchpad-common.md)
- [Variant Playbook (Mac)](variant-playbook-mac.md)
- [Variant Playbook (Windows)](variant-playbook-windows.md)
- [Scenario Validation Matrix](scenario-validation-matrix.md)
