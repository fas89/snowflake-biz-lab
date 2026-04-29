# Path B — AI Telco Silver Import Demo

This workspace is the starting point for the AI/MCP-forged silver variants (**B1** and **B2**). B1 is generated at run time by `task b1:forge:ai`; B2 is generated at run time by `task b2:forge:mcp`.

## Layout

```text
variants/
  B1-ai-reference-external/       # B1: AI forges a silver contract with external dbt and generated schedule assets
    subscriber360-external/       # live AI output lands here during the B1 playbook
  B2-ai-generate-in-workspace/    # B2: MCP reads seeded Snowflake metadata and generates dbt/airflow in the workspace
prompts/
  ai-reference-external.md        # The spoken prompt for the B1 forge step
  ai-generate-in-workspace.md     # The spoken prompt for the B2 forge step
sources/
  telco-stage-load.ddl.sql        # deterministic seeded Snowflake DDL snapshot
```

B1's `subscriber360-external` folder is pre-created but intentionally does not ship a ready-made contract. The B1 playbook calls `task b1:forge:ai`, which writes the live AI contract and preserves raw provider output under `runtime/generated/ai-forge/`.

B2's `subscriber360-generated` folder is also pre-created without a ready-made contract. The B2 playbook calls `task b2:forge:mcp`, which starts the forge-cli MCP server, reads the seeded Snowflake schema, writes the raw MCP model under `runtime/generated/mcp-forge/`, and generates the dbt/Airflow/Jenkins assets inside the product workspace.

The DDL snapshot is used as B1's seeded-data context:

```bash
task b1:forge:ai -- --provider gemini --model gemini-2.5-flash
task b2:forge:mcp
```

## Running A Variant

See the variant playbook for the commands: [Variant Playbook (Mac)](../../../docs/variant-playbook-mac.md) or [Variant Playbook (Windows)](../../../docs/variant-playbook-windows.md).
