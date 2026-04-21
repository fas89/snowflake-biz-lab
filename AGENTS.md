# AGENTS.md — Community Guide for AI Agents and Contributors

> How AI coding agents, copilots, and contributors should work in `snowflake-biz-lab`.

---

## What This Repo Is

`snowflake-biz-lab` is a Snowflake-first telco lab for:

- generating and loading realistic telco source data
- applying Horizon-friendly table and column metadata
- running a local demo platform with Airflow, dbt docs, Jenkins, and Entropy / DMM
- validating real FLUID behavior against scenario-driven demo workspaces

This repo is not the FLUID CLI implementation. It is the lab and demo environment around FLUID.

The main operator story is:

```text
seed source data -> validate contract -> plan -> verify plan -> apply/build -> generate CI -> publish
```

---

## How This Repo Is Organized

Focus on these areas first:

- `docs/`
  Shared setup, launchpads, troubleshooting, plan checks, scenario validation, and FLUID gap tracking.
- `seed/`
  Source-data generation, Snowflake loading, reset, and verification.
- `governance/`
  Metadata rendering, application, and verification for Snowflake/Horizon visibility.
- `deploy/docker/`
  Local platform stack for Airflow, dbt docs, Jenkins, catalogs, and supporting services.
- `fluid/`
  Contracts, prompts, runbooks, fixtures, and generated/reporting support for the FLUID demo.
- `fluid/fixtures/workspaces/`
  Tracked templates for the demo GitLab workspaces. `task workspaces:bootstrap` copies them into `./gitlab/`.
- `runtime/`
  Ignored local runtime files such as env files, generated secrets, and local helper state.

The demo workspaces live INSIDE the lab repo at `./gitlab/` (gitignored). They are materialized by `task workspaces:bootstrap` from the tracked templates:

- `gitlab/path-a-telco-silver-product-demo` (path A — reference-mapped silver)
- `gitlab/path-b-ai-telco-silver-import-demo` (path B — AI-forged silver)

Changes that should persist across fresh clones must be made in `fluid/fixtures/workspaces/`, not in `./gitlab/`. The bootstrap script initializes a local git repo inside each copied workspace so Jenkins' file-SCM can clone it. `task workspaces:reset` wipes and re-bootstraps. `scripts/reset_demo_state.py` triggers the same re-bootstrap by default.

---

## The Two FLUID Tracks

This repo supports two operator tracks:

### `demo-release`

Use this for:

- sandboxed demo validation
- release-truth behavior
- presenter rehearsals
- audience-facing runbooks

This track should use the released `data-product-forge` package path.

### `dev-source`

Use this for:

- investigating FLUID behavior
- fixing FLUID issues
- retesting the scenario matrix against source changes
- contributor workflows against the current `forge-cli` working tree

This track is for engineering iteration, not for hiding demo problems behind local-only behavior.

---

## Launchpads And Scenario Vocabulary

Start with:

- `docs/launchpad-common.md`

Then use one platform-specific launchpad:

- `docs/demo-release-launchpad-mac.md`
- `docs/demo-release-launchpad-windows.md`
- `docs/dev-source-launchpad-mac.md`
- `docs/dev-source-launchpad-windows.md`

Each track launchpad is a thin launcher that bootstraps its FLUID runtime and then hands off to the shared variant playbook:

- `docs/variant-playbook-mac.md` — shared Bronze / A1 / A2 / B1 / B2 commands for both tracks on Mac
- `docs/variant-playbook-windows.md` — same for Windows

Shared recovery runbook:

- `docs/launchpad-recovery.md` — DMM publish, Jenkins re-provision, `fluid apply` retry, full reset

Keep the repo's shared scenario vocabulary consistent across docs, code, and conversation:

- `bronze`
  Seed-source contract published from the lab
- `A1 external reference`
  Silver contract referencing shared dbt and Airflow assets outside the product folder
- `A2 internal reference`
  Silver contract packaging dbt and Airflow assets inside the product folder
- `B1 AI external reference`
  AI-created contract referencing dbt and Airflow assets elsewhere in Git
- `B2 AI generated assets`
  AI-created contract that generates dbt and Airflow assets in the workspace

Do not rename these scenarios casually. The launchpads, validation matrix, and demo story rely on this shared language.

---

## FLUID Limitation Rule

If you discover a FLUID limitation while working in this repo:

1. Stop and call it out clearly.
2. Ask whether to:
   - implement it in the current `forge-cli` working tree
   - or document it in `docs/fluid-gap-register.md`
   - or create an issue in `forge-cli`: <https://github.com/Agenticstiger/forge-cli/issues>
3. Do not add demo workarounds unless the user explicitly asks for one.

This is a strict repo rule. The goal is to keep the demo honest and the FLUID gaps visible.

When documenting a FLUID gap:

- describe the desired behavior
- describe the current observed behavior
- explain why it matters in the demo
- point to likely `forge-cli` areas to change later
- define clear acceptance criteria

Do not bury a FLUID limitation inside launchpad prose without also surfacing it through this decision flow.

---

## Demo Integrity Rules

- Keep the demo reproducible and clean.
- Do not silently reshape the demo around current FLUID limitations.
- Prefer fixing the real issue or documenting the gap over inventing side paths.
- Keep the contract as the source of truth for lineage and published behavior.
- Treat plan verification as a required gate, not a suggestion.
- Keep the operator story aligned across launchpads, scenario docs, and workspace READMEs.

If a step fails, preserve the intended story first. Report the true blocker instead of improvising a new flow.

---

## Mutation And Safety Rules

- Never commit secrets, tokens, passwords, or machine-specific runtime files.
- Respect ignored local files such as:
  - `.env`
  - `.env.catalogs`
  - `.env.jenkins`
  - `runtime/generated/fluid.local.env`
  - local launchpad path files under `runtime/generated/`
- Avoid destructive git commands such as `git reset --hard` or `git checkout --` unless explicitly requested.
- Do not overwrite user changes in a dirty worktree.
- If multiple repos are involved, keep ownership clear:
  - lab and demo changes belong here
  - FLUID implementation changes belong in the current `forge-cli` working tree
- Keep tracked docs publishable:
  - no personalized local paths
  - no personal branch names
  - no local-only assumptions written as universal truth

---

## Docs Maintenance Rules

When behavior changes, update the docs that define that behavior in the same change.

At minimum:

- shared setup/reset changes belong in `docs/launchpad-common.md`; variant command changes belong in `docs/variant-playbook-mac.md` and `docs/variant-playbook-windows.md`; recovery runbook changes belong in `docs/launchpad-recovery.md`; the four track launchpads should stay thin launchers that only bootstrap their FLUID runtime and hand off
- scenario-flow changes should stay aligned with the scenario validation matrix
- command-shape changes should be reflected in `docs/command-reference.md`
- new FLUID limitations should go through the FLUID limitation rule above

Keep docs concise, operator-friendly, and community-ready. Prefer shared vocabulary over ad hoc phrasing.

---

## Verification Expectations

After changing demo behavior, validate the affected path.

When scenario behavior changes, verify the relevant parts of the end state:

- plan generation and plan review path
- Snowflake target database/schema behavior
- Airflow visibility when a DAG is expected
- dbt docs visibility when a dbt project is expected
- Jenkins visibility when a generated pipeline is expected
- marketplace publication and lineage rendering when publish behavior is in scope

When a change affects only one track, verify that track directly. When it changes shared launchpad behavior or scenario vocabulary, verify both `demo-release` and `dev-source` docs still agree.

---

## Recommended Reading Order For Agents

1. `README.md`
2. `docs/launchpad-common.md`
3. The relevant platform launchpad
4. `docs/plan-verification-checklist.md`
5. `docs/scenario-validation-matrix.md`
6. `docs/fluid-gap-register.md`

Use that order unless the user asks for a narrower task.
