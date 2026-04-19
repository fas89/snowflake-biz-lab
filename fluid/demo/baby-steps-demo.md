# Baby Steps Demo

Use this as the short install-first warm-up before the full local-Mac demo.

## Step 1: Fresh Terminal And Install

```bash
cd ~/Desktop
mkdir -p fluid-baby-steps
cd fluid-baby-steps
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ data-product-forge
fluid version
fluid doctor
```

Checkpoint:

- you have shown the true beginning of the story
- `fluid version` proves the released CLI

## Step 2: Create The Tiny First Contract

```bash
fluid init hello-snowflake --provider snowflake --quickstart --yes
cd hello-snowflake
fluid validate contract.fluid.yaml
fluid plan contract.fluid.yaml --html
```

Checkpoint:

- the audience sees that FLUID starts from a contract
- you have a tiny first success before switching to the larger telco story

## Step 3: Move To The Real Demo

When you are ready to continue into the full target end-state story, jump to [Mac Greenfield Demo](mac-greenfield-demo.md).
