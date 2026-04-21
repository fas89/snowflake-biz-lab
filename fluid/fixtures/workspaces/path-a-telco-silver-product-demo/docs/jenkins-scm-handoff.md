# Jenkins SCM Handoff

The current lab story for Jenkins is:

1. Generate a `Jenkinsfile` from the contract with `fluid generate ci --system jenkins`.
2. Commit that generated `Jenkinsfile` into this GitLab workspace repo.
3. Push the workspace repo to GitLab.
4. Let Jenkins discover and run the generated pipeline from SCM.

This is the supported demo path today.

It is intentionally different from a future FLUID enhancement where `fluid apply` could trigger Jenkins directly.

If this workspace started as a local scaffold instead of a GitLab clone, initialize Git and push the workspace once before you expect Jenkins to discover anything from SCM.

## Why This Model

- It keeps the generated CI artifact versioned in Git.
- It matches the GitLab-first workspace story in this lab.
- It makes the demo reproducible because Jenkins reads the same repo state that the audience can inspect.

## Recommended Jenkins Job Types

- **Pipeline from SCM**
  - best for one known variant path
- **Multibranch Pipeline**
  - best when the GitLab repo will carry branches or multiple evolving variants

## Recommended Script Paths

- `variants/external-reference/Jenkinsfile`
- `variants/internal-reference/Jenkinsfile`

## Operator Flow

After `fluid generate ci`:

```bash
git add .
git commit -m "Update generated Jenkins pipeline"
git push
```

Then in Jenkins:

- trigger a scan or build on the GitLab-backed job
- confirm Jenkins picks up the generated `Jenkinsfile`
- confirm the job runs from the expected script path

## What Is Not Wired Yet

- `fluid apply` does not directly trigger Jenkins in this lab.
- Jenkins does not auto-read sibling local workspaces as the primary demo path.

That direct apply-to-Jenkins handoff remains a future FLUID enhancement and stays tracked in the FLUID gap register.
