# B1 Live AI Product Directory

This directory is intentionally light in the tracked workspace template.

Run `task b1:forge:ai` from the lab repo to create the live AI-generated
`contract.fluid.yaml` here, together with the raw forge receipt under
`runtime/generated/ai-forge/`.

The generated contract is then used by the B1 playbook to generate the
transformation preview, Airflow schedule, Jenkinsfile, plan, apply, verify, and
publish steps.
