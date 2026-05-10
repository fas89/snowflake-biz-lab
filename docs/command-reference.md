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
task pre1:demo
task pre2:demo
task pre3:demo
task pre:all:demo
task b1:forge
task b2:forge
task c1:forge
task c1:demo
task dbt:docs:refresh SCENARIO=A1
task catalogs:reset
task jenkins:sync SCENARIO=pre1
task jenkins:build SCENARIO=pre1
task jenkins:sync SCENARIO=A1
task jenkins:build SCENARIO=A1
task jenkins:sync SCENARIO=A2
task jenkins:build SCENARIO=A2
task jenkins:sync SCENARIO=B1
task jenkins:build SCENARIO=B1
task jenkins:sync SCENARIO=B2
task jenkins:build SCENARIO=B2
task jenkins:sync SCENARIO=C1
task jenkins:build SCENARIO=C1
```

The 8 active scenarios are: `pre1`, `pre2`, `pre3` (Pre-* acquisition: dlt / PyAirbyte / Meltano), `A1`, `A2` (silver via curated dbt), `B1`, `B2` (silver via AI-forged dbt), `C1` (gold composition CDP). Older `b1:forge:ai` + `b2:forge:mcp` Taskfile entries were superseded by the consolidated `b1:forge` / `b2:forge` / `c1:forge` drivers in `scripts/run_ai_forge_b1.py`, `scripts/run_mcp_forge_b2.py`, and `scripts/run_compose_forge_c1.py`.

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
"$FLUID_CLI" generate ci contract.fluid.yaml --system jenkins --install-mode "$JENKINS_INSTALL_MODE" --default-publish-target datamesh-manager --runner-host-override host.docker.internal --out Jenkinsfile
# For A1 and B1, add:
#   --no-verify-strict-default --publish-stage-default --no-publish-include-env
# For pre-2 (Airbyte) and any other engine='airbyte' contract:
#   The engine_specs registry auto-injects AIRBYTE_PROJECT_DIR + AIRBYTE_TEMP_DIR
#   into the Jenkinsfile env block AND surfaces a "REQUIRES: /var/run/docker.sock"
#   comment. The lab's Jenkins container handles both via deploy/docker/jenkins/
#   Dockerfile (root + runuser ENTRYPOINT, chmod docker.sock) + the symmetric
#   /tmp/airbyte bind in deploy/docker/docker-compose.yml. See
#   docs/architecture.md and docs/jenkins-scm-handoff.md for the full DinD story.
# Other useful flags:
#   --list-engines              print the supported (engine x source x sink) matrix
#   --runner-host-override HOST  rewrite contract `host: localhost` to a host-
#                                reachable address inside containerised runners
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
# For B1, run `task b1:forge` first, then run the same generate command from:
# "$EXISTING_DBT_WORKSPACE/variants/B1-ai-reference-external/subscriber360-external"
# then use: task jenkins:sync SCENARIO=B1 && task jenkins:build SCENARIO=B1
# For B2, run `task b2:forge` first. That task writes the generated
# Jenkinsfile under:
# "$EXISTING_DBT_WORKSPACE/variants/B2-ai-generate-in-workspace/subscriber360-generated"
# then use: task jenkins:sync SCENARIO=B2 && task jenkins:build SCENARIO=B2
# For C1 (compose-CDP), run `task c1:demo` end-to-end (chains b1:forge + b2:forge
# + c1:forge + sync + build). Or stage-by-stage: `task c1:forge` then
# `task jenkins:sync SCENARIO=C1 && task jenkins:build SCENARIO=C1 -- --param APPLY_MODE=amend`.
```

In the demo-release track, `task jenkins:sync` and `task jenkins:build` read `runtime/generated/demo-release.env`, so Jenkins uses the same resolved TestPyPI package as your local `fluid` command without extra `--param` flags.

## Related Docs

- [Launchpad Common](launchpad-common.md)
- [Variant Playbook (Mac)](variant-playbook-mac.md)
- [Variant Playbook (Windows)](variant-playbook-windows.md)
- [Scenario Validation Matrix](scenario-validation-matrix.md)
