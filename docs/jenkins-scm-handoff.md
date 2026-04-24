# Jenkins SCM Handoff

The lab now creates Jenkins jobs on demand instead of seeding them at startup.

## Supported Flow

1. Generate a `Jenkinsfile` from the contract with `fluid generate ci --system jenkins --default-publish-target datamesh-manager`. The `--default-publish-target` flag bakes the catalog name into the Stage 10 `${PUBLISH_TARGETS:-datamesh-manager}` shell fallback so the very first Jenkins SCM build (which runs before the `parameters { }` block exports env vars) still publishes to DMM instead of failing with an empty target list.
   For A1 only, generate the file with `--no-verify-strict-default --publish-stage-default --no-publish-include-env` so the A1 lab defaults are emitted directly instead of patching the file afterward.
2. Commit that `Jenkinsfile` in the local workspace repo.
3. Run `task jenkins:sync SCENARIO=A1` or `task jenkins:sync SCENARIO=A2`.
4. Run `task jenkins:build SCENARIO=A1` or `task jenkins:build SCENARIO=A2`.

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
- targets the synced A1 or A2 job and triggers Jenkins through `buildWithParameters`
- carries the lab default `PUBLISH_TARGETS=datamesh-manager` and, for demo-release, the resolved TestPyPI install parameters unless you override them with `task jenkins:build SCENARIO=A1 -- --param KEY=VALUE`
- refuses to fall back to plain `/build` if Jenkins would drop required parameter overrides
- waits for the queue item to start, then waits for the build result
- prints the final build URL and the console tail, and exits non-zero on failure

## Fixed Job Mapping

| Scenario | Jenkins job | SCM repo inside Jenkins | Script path |
| --- | --- | --- | --- |
| A1 | `A1-external-reference` | `/workspace/gitlab/path-a-telco-silver-product-demo/.git` | `variants/A1-external-reference/Jenkinsfile` |
| A2 | `A2-internal-reference` | `/workspace/gitlab/path-a-telco-silver-product-demo/.git` | `variants/A2-internal-reference/Jenkinsfile` |

The Jenkins container reads the repo from the local bind mount. No `git push` is required for the lab flow.

## Scenario Defaults

- A1 is lab-tuned to generate `VERIFY_STRICT=false`, `RUN_STAGE_10_PUBLISH=true`, and a `fluid publish` command without the stage-level `--env` flag. The reference dbt assets build and publish successfully, but the live Snowflake tables still report nullable-vs-required mismatches that would fail a strict verify gate.
- A2 keeps the generated strict default. Its Jenkins run is expected to stop at stage `9 · verify` on `fluid verify ... --strict`, which is part of the teaching flow rather than a broken lab.

## What Is Not Wired

- `fluid apply` does not trigger Jenkins directly
- multibranch or repo auto-discovery is not configured
- B1 and B2 are not part of the supported Jenkins flow in this lab
