# Path B — AI Telco Silver Import Demo

This workspace is the starting point for the AI-forged silver variants (**B1** and **B2**). It intentionally ships **empty** — the operator creates the silver product live during the demo using `fluid forge` (live mode) or a captured golden contract (demo mode).

## Layout

```text
variants/
  B1-ai-reference-external/       # B1: AI forges a silver contract that references external dbt/airflow
  B2-ai-generate-in-workspace/    # B2: AI forges a silver contract and generates dbt/airflow in the workspace
prompts/
  ai-reference-external.md        # The spoken prompt for the B1 forge step
  ai-generate-in-workspace.md     # The spoken prompt for the B2 forge step
```

The `fluid init <name> --provider snowflake --yes` step inside each `variants/Bx-*` folder creates the actual product subdirectory (e.g. `subscriber360-external`).

## Running A Variant

See the variant playbook for the commands: [Variant Playbook (Mac)](../../../docs/variant-playbook-mac.md) or [Variant Playbook (Windows)](../../../docs/variant-playbook-windows.md).
