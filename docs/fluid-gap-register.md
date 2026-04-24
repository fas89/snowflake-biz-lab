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

## `apply --build` requires a raw build ID

- Desired demo behavior:
  `fluid apply --build` should either accept the contract's primary build implicitly or offer a first-class build selector that is easy to use from the contract and plan output.
- Current observed behavior:
  In the current `forge-cli` dev runtime, `fluid apply` expects `--build <build-id>`. The runbooks originally treated `--build` like a boolean flag, which is easy to misread and forces operators to inspect `builds[].id` manually.
- Why it matters in the demo:
  It creates friction right after plan verification, and it makes the apply step feel less native than the rest of the FLUID flow.
- Likely `forge-cli` area to change later:
  `fluid_build/cli/apply.py`, contract/build resolution utilities, and plan/report output that could surface a default or selected build more explicitly.
- Acceptance criteria:
  An operator can run `fluid apply` for a single-build contract without manually copying a raw build ID out of the contract, or the CLI clearly presents the selectable build IDs in a first-class way.

## dbt repository builds fall into the legacy Python-script executor

- Desired demo behavior:
  A contract build with `engine: dbt`, a `repository` pointing at a dbt project, and `properties.model` pointing at a dbt model should execute as a dbt build or run inside `fluid apply`.
- Current observed behavior:
  In the current `forge-cli` dev runtime, `fluid apply --build <build-id>` routes into the absorbed legacy `execute` path. That path resolves builds as Python scripts like `<repository>/<model>.py`, so a dbt build such as `repository: ../../reference-assets/dbt_dv2_subscriber360` and `model: mart_subscriber_health_scorecard` is treated as a missing file `../../reference-assets/dbt_dv2_subscriber360/mart_subscriber_health_scorecard.py`.
- Why it matters in the demo:
  The contract says the build is dbt-based, but the current runtime does not execute it natively. That breaks the most important “validate -> plan -> apply/build” moment in the silver demo story.
- Likely `forge-cli` area to change later:
  `fluid_build/cli/apply.py`, `fluid_build/cli/execute.py`, and any build-engine dispatch layer that should distinguish Python, SQL, and dbt builds instead of forcing them all through script resolution.
- Acceptance criteria:
  `fluid apply --build <build-id>` recognizes `engine: dbt` builds and executes the referenced dbt project natively, including model selection, runtime vars, tests, and clear reporting, without requiring a `.py` script shim.

## Native dbt execution assumes a local adapter-capable dbt runtime

- Desired demo behavior:
  A dbt-based build can run natively from `fluid apply --build <build-id>` whether the operator uses a local dbt installation or a containerized/project-specific dbt runtime.
- Current observed behavior:
  After native dbt dispatch is enabled, the current runtime shells out to `dbt build` on the local machine. In this lab that reaches the next failure immediately if the local dbt installation does not include the required adapter, for example `Could not find adapter type snowflake!`.
- Why it matters in the demo:
  The FLUID contract is ready to execute the dbt build, but the demo environment may already have a working dbt runtime inside Docker rather than on the host machine. The current runtime does not provide a first-class way to target that execution environment.
- Likely `forge-cli` area to change later:
  `fluid_build/cli/execute.py` and related build-engine configuration so dbt execution can support richer command prefixes, container runners, or provider-aware runtime selection instead of assuming a single local `dbt` executable.
- Acceptance criteria:
  An operator can configure a dbt build to run against the intended runtime, including local and containerized dbt environments, without patching the contract or relying on a host-specific adapter install.

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
- Interim demo workaround (2026-04-20):
  `fluid forge` output varies across runs because the underlying LLM call is nondeterministic, which is unsafe for a live stage demo. Until `forge-cli` exposes a seed or deterministic-replay flag, the launchpads copy a captured golden contract from `fluid/fixtures/forge-golden/B1-ai-reference-external/` (and `B2-ai-generate-in-workspace/` for scenario B2) into the workspace instead of calling the live LLM. The live-mode commands remain in the launchpad as commented-out alternatives, and `fluid/fixtures/forge-golden/README.md` documents how to refresh the golden off-stage. Remove the workaround once forge-cli supports replay natively.

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

## Airflow generation + native local schedule sync

- Desired demo behavior:
  Existing Airflow DAG assets or generated schedule outputs land where the local Airflow instance can consume them immediately from the documented local destination.
- Current observed behavior:
  `fluid schedule-sync --scheduler airflow --destination <local path>` works, but the operator still has to pick and clear the destination explicitly in the lab docs.
- Why it matters in the demo:
  The orchestration step feels strongest when the generated DAGs become visible in Airflow right away.
- Likely `forge-cli` area to change later:
  `fluid_build/cli/schedule_sync.py`, scheduler output defaults, and any future workspace-aware sync helpers.
- Acceptance criteria:
  A selected DAG directory from the active workspace appears in local Airflow without extra manual destination cleanup or path wrangling.

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

## `fluid init --yes` still blocks on interactive mode selection (0.8.0a1)

- Desired demo behavior:
  `fluid init <name> --yes --provider snowflake` runs non-interactively and scaffolds the project with default settings.
- Current observed behavior:
  Observed in TestPyPI `data-product-forge==0.8.0a1`: the command still prompts `Choose [1/2/3/4] (2):` for the init mode (Quickstart / Let AI design / Template / Empty). With non-TTY stdin, the read fails immediately and the command crashes with `init_failed: EOF when reading a line`. `--yes` is documented as "Skip confirmation prompts" but does not skip this mode selector.
- Why it matters in the demo:
  The B1/B2 launchpad step `fluid init subscriber360-external --provider snowflake --yes` is unrunnable as-scripted. The lab's variant playbook treats `fluid init` as a one-liner; an interactive blocker breaks rehearsal automation, CI validation, and any scripted replay.
- Likely `forge-cli` area to change later:
  `fluid_build/cli/init.py` — `--yes` (and/or `--non-interactive`) should short-circuit the top-level mode prompt, defaulting to mode 2 (AI-designed) when a name is supplied, or require `--quickstart` / `--blank` / `--template` to disambiguate with a clear error rather than hanging on stdin.
- Acceptance criteria:
  `fluid init NAME --provider snowflake --yes </dev/null` completes without stdin reads and scaffolds the same output the interactive default-mode path would have. Covered by a CLI integration test that runs without a TTY.
- Interim demo workaround (2026-04-21):
  Use `fluid init NAME --blank --provider snowflake --yes` to bypass the mode selector, then follow with `fluid forge` when the AI-authoring step is wanted.

## `fluid forge --context` resolves relative paths from wrong cwd + error handler crashes (0.8.0a1)

- Desired demo behavior:
  `fluid forge --provider snowflake --domain telco --target-dir . --context ../../prompts/ai-reference-external.md` loads the prompt file (resolved relative to the current working directory) and uses it as AI context for the forge run. If the path is wrong, a clear error message is shown.
- Current observed behavior:
  Observed in `data-product-forge==0.8.0a1` running from `$EXISTING_DBT_WORKSPACE/variants/B1-ai-reference-external/subscriber360-external`: forge reports `Context file not found: ../../prompts/ai-reference-external.md` even though the file exists relative to the invocation cwd (the relative-path resolution appears to use a different base directory). The error-handling path in `fluid_build/cli/forge_context.py:304` and `forge_context.py:353` then crashes with `TypeError: CLIError.__init__() missing 1 required positional argument: 'event'` because the `CLIError` constructor signature has changed but these two call sites still pass a single positional message. The operator sees the TypeError, not the original "file not found" message.
- Why it matters in the demo:
  `--context` is the natural way to drive `fluid forge` with a curated prompt markdown file (the variant playbook's `cat ../../prompts/*.md` step exists precisely because forge should consume this content). The path bug plus the broken error path together mean the operator cannot pass a prompt file and cannot understand why when it fails.
- Likely `forge-cli` area to change later:
  `fluid_build/cli/forge_context.py` — resolve relative `--context` paths against `os.getcwd()` (or document the true base explicitly), and update both `raise context_error_cls(...)` sites to match the current `CLIError.__init__` signature (supply the `event` argument or use a builder helper).
- Acceptance criteria:
  Passing a relative `--context` path from any cwd loads the file when it exists on disk, and a missing path raises a user-visible "Context file not found: X" error without a secondary `TypeError`. Covered by a CLI integration test that invokes `fluid forge --context path/that/does/not/exist` and asserts clean error output.

## Installed `fluid_build` package missing `llm_models.json` (0.8.0a1)

- Desired demo behavior:
  Every `fluid ...` command runs without spurious warnings when the package is installed from TestPyPI.
- Current observed behavior:
  Observed in `data-product-forge==0.8.0a1`: every invocation prints `Could not load model catalog .../fluid_build/cli/llm_models.json: [Errno 2] No such file or directory`. The file is referenced at runtime but not included in the wheel's `package_data`. Commands still work in demo mode; the warning clutters the terminal and can confuse presenters.
- Why it matters in the demo:
  A warning on every command makes the release look broken mid-demo. The Jenkins console log is especially noisy because each pipeline stage shells out to `fluid`.
- Likely `forge-cli` area to change later:
  `fluid_build/cli/llm_models.json` — include the JSON in `pyproject.toml`'s `[tool.setuptools.package-data]` (or equivalent `MANIFEST.in`). Also consider a code-level fallback in `fluid_build/cli/forge.py` that falls back to an embedded default catalog when the file is missing.
- Acceptance criteria:
  Installing `data-product-forge` from TestPyPI into a fresh venv and running `fluid version` prints no "Could not load model catalog" warning.

## Fragment-first forge output breaks build-ID extraction helpers

- Desired demo behavior:
  After `fluid forge`, downstream steps (plan, apply, helper scripts) can resolve the primary build ID without the operator having to open fragment files by hand.
- Current observed behavior:
  Observed in `data-product-forge==0.8.0a1`: `fluid forge` emits a "fragment-first (modular)" contract whose top-level `builds:` is `[{ $ref: ./fragments/builds/customer_party_mart.yaml }]`. The lab helper `scripts/get_first_build_id.py` reads only the top-level `builds[*].id` key and prints `No builds[] entry found in contract.fluid.yaml`. `fluid apply --build` then has no obvious source for the build ID unless the operator reads the fragment manually.
- Why it matters in the demo:
  The B1/B2 launchpad line `BUILD_ID="$(python3 "$LAB_REPO/scripts/get_first_build_id.py" contract.fluid.yaml)"` fails for every fragment-first forge output, even though `fluid validate`/`fluid plan` succeed. The operator has to cat the fragment file to pick up `customer_party_mart` and then retype it into `fluid apply --build`. That kills the one-command apply story.
- Likely `forge-cli` area to change later:
  Either (a) expose a first-class CLI that prints the primary/selected build ID given a contract — for example `fluid inspect build-id contract.fluid.yaml` — which would traverse fragments internally, or (b) have `fluid apply` pick the single-build case implicitly (already tracked under "apply --build requires a raw build ID"), or (c) extend `scripts/get_first_build_id.py` in this repo to follow `$ref` fragments. Option (a) is the cleanest because it also fixes CI pipelines, tests, and any third-party automation.
- Acceptance criteria:
  With a forge-produced fragment-first contract, a supported command prints the primary build ID reliably (and the `apply --build` step can consume it), without the operator opening fragment YAML by hand.
