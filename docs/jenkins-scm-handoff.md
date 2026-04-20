# Jenkins SCM Handoff

The current lab story for Jenkins is:

1. Generate a `Jenkinsfile` from the contract with `fluid generate ci --system jenkins`.
2. Commit that generated `Jenkinsfile` into the GitLab workspace repo on disk.
3. Let Jenkins discover and run the generated pipeline from that local repo.

This is the supported demo path today.

It is intentionally different from a future FLUID enhancement where `fluid apply` could trigger Jenkins directly.

## Why This Model

- It keeps the generated CI artifact versioned in Git.
- It matches the GitLab-first workspace story in this lab.
- It makes the demo reproducible because Jenkins reads the same repo state that the audience can inspect.

## How Jobs Get Into Jenkins

`task jenkins:up` auto-provisions three pipelines via Jenkins Configuration-as-Code and the `job-dsl` plugin:

| Jenkins job                 | Workspace repo                                           | Script path                                                            |
| --------------------------- | -------------------------------------------------------- | ---------------------------------------------------------------------- |
| `A1-external-reference`     | `gitlab/path-a-telco-silver-product-demo`                       | `variants/A1-external-reference/Jenkinsfile`                              |
| `A2-internal-reference`     | `gitlab/path-a-telco-silver-product-demo`                       | `variants/A2-internal-reference/Jenkinsfile`                              |
| `B1-subscriber360-external` | `gitlab/path-b-ai-telco-silver-import-demo`                        | `variants/B1-ai-reference-external/subscriber360-external/Jenkinsfile`    |

The gitlab workspaces are mounted read-only at `/workspace/gitlab/` inside the Jenkins container. The host path is configurable via `DEMO_WORKSPACES_DIR` (defaults to the sibling `gitlab/` directory).

The JobDSL scripts live in `jenkins/casc/jenkins.yaml`. Adding a job is a one-file YAML edit + `task jenkins:up` restart.

## Recommended Script Paths

For the ready-made workspace:

- `variants/A1-external-reference/Jenkinsfile`
- `variants/A2-internal-reference/Jenkinsfile`

For the AI workspace:

- `variants/B1-ai-reference-external/subscriber360-external/Jenkinsfile`
- `variants/B2-ai-generate-in-workspace/subscriber360-generated/Jenkinsfile`

## Operator Flow

After `fluid generate ci`:

```bash
git add .
git commit -m "Update generated Jenkins pipeline"
```

Then in Jenkins at [http://localhost:8081](http://localhost:8081):

- open the matching job (`A1-external-reference`, `A2-internal-reference`, or `B1-subscriber360-external`)
- click **Build Now**
- confirm Jenkins reads the generated `Jenkinsfile` from the expected script path

A `git push` is not required — the SCM URL points at the local `file:///workspace/gitlab/<repo>/.git`, so Jenkins sees the committed state directly.

## What Is Not Wired Yet

- `fluid apply` does not directly trigger Jenkins in this lab.
- Multibranch Pipeline auto-discovery is not configured; the three jobs are single-branch Pipeline-from-SCM.

That direct apply-to-Jenkins handoff remains a future FLUID enhancement and stays tracked in the FLUID gap register.
