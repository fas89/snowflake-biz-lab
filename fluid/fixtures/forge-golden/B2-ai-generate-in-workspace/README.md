# B2 MCP Marker

This folder intentionally does not contain a `contract.fluid.yaml` or generated
asset tree.

B2 is now generated at run time by `task b2:forge:mcp`. That command starts the
forge-cli MCP server, reads the lab's seeded Snowflake schema, writes the raw
MCP model under the scenario runtime directory, and generates the B2 dbt,
Airflow, and Jenkins assets inside the Path B workspace.

See [../README.md](../README.md) for the full refresh workflow.
