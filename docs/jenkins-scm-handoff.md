# Jenkins SCM Handoff

The lab now creates Jenkins jobs on demand instead of seeding them at startup.

## Supported Flow

1. Generate a `Jenkinsfile` from the contract with `fluid generate ci --system jenkins --default-publish-target datamesh-manager`. The `--default-publish-target` flag bakes the catalog name into the Stage 10 `${PUBLISH_TARGETS:-datamesh-manager}` shell fallback so the very first Jenkins SCM build (which runs before the `parameters { }` block exports env vars) still publishes to DMM instead of failing with an empty target list.
   For A1 and B1, generate the file with `--no-verify-strict-default --publish-stage-default --no-publish-include-env` so the lab defaults are emitted directly instead of patching the file afterward.
2. Commit that `Jenkinsfile` in the local workspace repo.
3. Run `task jenkins:sync SCENARIO=A1`, `task jenkins:sync SCENARIO=A2`, `task jenkins:sync SCENARIO=B1`, or `task jenkins:sync SCENARIO=B2`.
4. Run `task jenkins:build SCENARIO=A1`, `task jenkins:build SCENARIO=A2`, `task jenkins:build SCENARIO=B1`, or `task jenkins:build SCENARIO=B2`.

This keeps the generated CI artifact versioned in Git while making the first-run Jenkins dashboard truly empty.

In the `demo-release` track, the launchpad writes the resolved TestPyPI package and pip indexes to `runtime/generated/demo-release.env`. The Jenkins sync/build tasks read that file so the first Jenkins build uses the same released FLUID package as your local shell, without extra `--param` flags.

The Jenkins container also loads `runtime/generated/fluid.local.env` at startup so publish stages can use the live local `DMM_API_KEY`. If you rerun `task catalogs:bootstrap`, restart Jenkins before expecting publish stages to see the refreshed key.

## What `task jenkins:sync` Does

The task calls `scripts/sync_jenkins_job.py`, which:

- reads `.env` and `.env.jenkins`, with `.env.jenkins` taking precedence
- reads `runtime/generated/demo-release.env` when the demo-release launchpad created it
- validates that the local workspace repo and generated `Jenkinsfile` exist
- prints the target Jenkins URL, job name, repo, and script path
- creates or updates a single Pipeline-from-SCM job through the Jenkins HTTP API
- seeds bootstrap build parameters such as `PUBLISH_TARGETS` and, for demo-release, the resolved `FLUID_PACKAGE_SPEC` and pip index values
- does not trigger a build

## What `task jenkins:build` Does

The task calls `scripts/run_jenkins_build.py`, which:

- reads `.env` and `.env.jenkins`, with `.env.jenkins` taking precedence
- reads `runtime/generated/demo-release.env` when the demo-release launchpad created it
- targets the synced A1, A2, B1, or B2 job and triggers Jenkins through `buildWithParameters`
- carries the lab default `PUBLISH_TARGETS=datamesh-manager` and, for demo-release, the resolved TestPyPI install parameters unless you override them with `task jenkins:build SCENARIO=A1 -- --param KEY=VALUE`
- refuses to fall back to plain `/build` if Jenkins would drop required parameter overrides
- waits for the queue item to start, then waits for the build result
- prints the final build URL and the console tail, and exits non-zero on failure

## Fixed Job Mapping

| Scenario | Jenkins job | SCM repo inside Jenkins | Script path |
| --- | --- | --- | --- |
| A1 | `A1-external-reference` | `/workspace/gitlab/path-a-telco-silver-product-demo/.git` | `variants/A1-external-reference/Jenkinsfile` |
| A2 | `A2-internal-reference` | `/workspace/gitlab/path-a-telco-silver-product-demo/.git` | `variants/A2-internal-reference/Jenkinsfile` |
| B1 | `B1-ai-reference-external` | `/workspace/gitlab/path-b-ai-telco-silver-import-demo/.git` | `variants/B1-ai-reference-external/subscriber360-external/Jenkinsfile` |
| B2 | `B2-ai-generate-in-workspace` | `/workspace/gitlab/path-b-ai-telco-silver-import-demo/.git` | `variants/B2-ai-generate-in-workspace/subscriber360-generated/Jenkinsfile` |

The Jenkins container reads the repo from the local bind mount. No `git push` is required for the lab flow.

## Scenario Defaults

- A1 is lab-tuned to generate `VERIFY_STRICT=false`, `RUN_STAGE_10_PUBLISH=true`, and a `fluid publish` command without the stage-level `--env` flag. The reference dbt assets build and publish successfully, but the live Snowflake tables still report nullable-vs-required mismatches that would fail a strict verify gate.
- A2 keeps the generated strict default. Its Jenkins run is expected to stop at stage `9 - verify` on `fluid verify ... --strict`, which is part of the teaching flow rather than a broken lab.
- B1 starts with `task b1:forge:ai`, then uses the same non-strict verify and publish defaults as A1, plus bootstrap parameters `APPLY_MODE=amend-and-build` and `APPLY_BUILD_ID=ai_subscriber360_external_build` so the Path B Jenkins run executes the external dbt build.
- B2 starts with `task b2:forge:mcp`, then uses the same non-strict verify and publish defaults as B1, plus bootstrap parameters `APPLY_MODE=amend-and-build` and `APPLY_BUILD_ID=ai_subscriber360_generated_build` so the Path B Jenkins run executes the generated in-workspace dbt build.

## Jenkins Container Privilege Model

The lab Jenkins container is intentionally root-at-PID-1 and chmods the bind-mounted Docker socket so PyAirbyte (pre-2) can spawn source connectors via the host daemon. The wrapper ENTRYPOINT then drops to the `jenkins` user via `runuser` for the controller process. This is **lab-only** — the Dockerfile and compose file both warn "NEVER do this in production". See [Architecture > Jenkins Container — Privilege Model](architecture.md#jenkins-container--privilege-model) for the full rationale.

The compose file also bind-mounts:

- `/var/run/docker.sock:/var/run/docker.sock` — gives the container root-equivalent on the host. Required for `engine: airbyte` contracts (PyAirbyte spawns sibling Docker containers).
- `/tmp/airbyte:/tmp/airbyte` — symmetric path on host and container. Required for the host docker daemon to find the connector config files PyAirbyte writes (Docker-in-Docker volume sharing pattern). See [Architecture > DinD Volume Sharing for PyAirbyte](architecture.md#dind-volume-sharing-for-pyairbyte).

## Generated Jenkinsfile env block

`fluid generate ci --system jenkins --runner-host-override host.docker.internal` emits these env vars into the Jenkinsfile's `environment {}` block via the forge-cli engine specs registry:

| Env var | Purpose | Engines that need it |
| --- | --- | --- |
| `FLUID_RUNNER_HOST_OVERRIDE` | Rewrites contract-author `host: localhost` to a host-reachable address (Docker Desktop = `host.docker.internal`). | All acquisition engines (dlt / PyAirbyte / Meltano source adapters). |
| `AIRBYTE_PROJECT_DIR` | Pins PyAirbyte's `Path.cwd()` cache to a writable bind-mounted dir (`/tmp/airbyte`). | airbyte only. |
| `AIRBYTE_TEMP_DIR` | Overrides PyAirbyte's `tempfile.gettempdir()` so connector config JSON lands in the bind-mounted dir (`/tmp/airbyte/tmp`). Required for DinD volume sharing. | airbyte only. |

For the runtime-notes block above the `environment {}` (Jenkinsfile `// REQUIRES:` comments), forge-cli reads these from the same registry. Adding a new engine = one entry in `_engine_specs.py` and every CI emitter picks it up.

## What Is Not Wired

- `fluid apply` does not trigger Jenkins directly
- multibranch or repo auto-discovery is not configured
- only the Jenkins emitter (not GitHub Actions / GitLab CI / Tekton / Azure / Bitbucket / CircleCI) consumes the engine specs registry today; for those CI systems, generated configs do not yet inject per-engine pip extras or runtime env vars
