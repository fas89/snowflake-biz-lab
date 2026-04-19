# FLUID Gap Register

This register documents the FLUID work that the repo expects you to implement later in `forge-cli`.

The goal here is simple: keep the demo docs aimed at the target end-state, and keep the current gaps visible and actionable.

The observations below should be rechecked against the latest `data-product-forge` TestPyPI release and the current `forge-cli` sources before each demo cycle.

## `apply -> Jenkins handoff`

- Desired demo behavior:
  `fluid apply` deploys the data product and hands off into the generated Jenkins deployment path.
- Current observed behavior:
  `fluid generate ci --system jenkins` writes a `Jenkinsfile`, and the current supported demo path is SCM pickup from GitLab. The current `fluid apply` surface still does not expose a Jenkins-specific handoff or trigger step.
- Why it matters in the demo:
  The story ends more cleanly if generated CI becomes a first-class deployment handoff instead of relying on a separate SCM job setup step.
- Likely `forge-cli` area to change later:
  `fluid_build/cli/generate_ci.py`, `fluid_build/cli/scaffold_ci.py`, `fluid_build/cli/apply.py`, and execution/reporting hooks around post-apply actions.
- Acceptance criteria:
  After `fluid generate ci --system jenkins`, `fluid apply` can either trigger the generated Jenkins path directly or emit a first-class Jenkins deployment handoff with workspace and plan context.

## AI `forge` for Snowflake + dbt silver aggregation

- Desired demo behavior:
  `fluid forge` creates a clean Snowflake silver-layer aggregated telco contract that is explicitly dbt-oriented and aligned to the seeded staging model.
- Current observed behavior:
  `fluid forge` is a general AI entrypoint with provider, domain, discovery, and target-dir options, but this repo does not yet have a deterministic Snowflake silver aggregation flow tied to the telco staging model.
- Why it matters in the demo:
  The greenfield story depends on AI-assisted authoring that feels purposeful rather than generic.
- Likely `forge-cli` area to change later:
  `fluid_build/cli/forge_modes.py`, Snowflake provider templates, transformation generation logic, and prompt scaffolding for domain-specific silver outputs.
- Acceptance criteria:
  A greenfield `fluid forge --provider snowflake --domain telco` flow can reliably scaffold a silver aggregated contract and the right dbt-oriented build references for this lab.

## Existing dbt reference flow

- Desired demo behavior:
  An existing dbt project can be referenced or imported cleanly, then refined with FLUID without losing the original dbt intent.
- Current observed behavior:
  `fluid import --dir ./dbt --provider snowflake` scans and generates contracts, but the import-to-refinement handoff is not yet a rehearsed end-to-end flow in this repo.
- Why it matters in the demo:
  The second variation should prove that FLUID works for both greenfield and brownfield teams.
- Likely `forge-cli` area to change later:
  dbt discovery and import logic, contract merge/update flows, and the way `forge` enriches imported contracts.
- Acceptance criteria:
  A user can import an existing dbt project, keep the relevant references, refine the result with AI assistance, and continue into schedule/CI generation without manual contract surgery.

## Airflow generation + local Mac workspace bridge

- Desired demo behavior:
  Generated Airflow artifacts land where the local Airflow instance can consume them immediately from the GitLab workspace on the Mac.
- Current observed behavior:
  `fluid generate schedule` can write to an output directory, and this repo now mounts one active workspace bridge into Airflow, but switching workspaces still requires explicit local alignment.
- Why it matters in the demo:
  The orchestration step feels strongest when the generated DAGs become visible in Airflow right away.
- Likely `forge-cli` area to change later:
  `fluid_build/cli/generate_schedule.py`, scheduler output defaults, and any future workspace-aware generation hooks.
- Acceptance criteria:
  A generated Airflow schedule from the active workspace appears in local Airflow without extra manual path wrangling beyond the documented workspace choice.

## Standards + marketplace path

- Desired demo behavior:
  OPDS, ODCS, and ODPS generation flow naturally into publication to the local Entropy / DMM marketplace.
- Current observed behavior:
  `fluid generate standard` and `fluid publish` are still separate concerns. The repo can demonstrate both, but the handoff is not yet one unified end-state workflow.
- Why it matters in the demo:
  The closing moment should show standards and marketplace publication as one coherent product story.
- Likely `forge-cli` area to change later:
  `fluid_build/cli/generate_standard.py`, `fluid_build/cli/datamesh_manager.py`, and any post-apply or publish orchestration hooks.
- Acceptance criteria:
  The contract can generate the standards artifacts you want to show, and the DMM publish path can use them or reference them in one clear workflow with minimal duplication.
