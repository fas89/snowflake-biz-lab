# Backup Demo

Use this when the room needs a shorter, safer story.

## When To Switch

Switch to this path when:

- TestPyPI is slow
- venue Wi-Fi is unstable
- you do not want to risk a live Snowflake mutation late in the session
- local Entropy or Jenkins is healthy, but you do not want to depend on every end-to-end step

## Step 1: Install From A Pre-Staged Wheel

Put the release wheel in `runtime/wheels/` before the event.

```bash
cd ~/Desktop
mkdir -p fluid-backup-demo
cd fluid-backup-demo
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install runtime/wheels/data_product_forge-*.whl
fluid version
fluid doctor --features-only
```

## Step 2: Prove The Platform And Seed State

```bash
cd "/Users/A200004702/Documents/Open-Source Community/snowflake-biz-lab"
task ps
task seed:verify
task metadata:verify
```

## Step 3: Tiny Scaffold

```bash
cd ~/Desktop/fluid-backup-demo
fluid init hello-snowflake --provider snowflake --quickstart --yes
cd hello-snowflake
fluid validate contract.fluid.yaml
fluid plan contract.fluid.yaml --html
```

## Step 4: Real Telco Contract Without Live Mutation

```bash
cd "/Users/A200004702/Documents/Open-Source Community/snowflake-biz-lab"
set -a
source runtime/generated/fluid.local.env
set +a
.venv.fluid-demo/bin/fluid validate fluid/contracts/telco_stage_seed/contract.fluid.yaml
.venv.fluid-demo/bin/fluid plan fluid/contracts/telco_stage_seed/contract.fluid.yaml --out fluid/generated/telco-stage-plan.json --html
```

This still shows:

- install
- version proof
- platform readiness
- real telco contract
- safe HTML plan before execution

If the room stabilizes later, you can still decide whether to run `apply`, standards export, or DMM publish.
