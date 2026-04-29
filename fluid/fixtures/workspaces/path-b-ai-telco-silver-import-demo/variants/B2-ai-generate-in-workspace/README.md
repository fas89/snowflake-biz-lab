# B2 — AI Forge With Generated Assets

The B2 path starts by running `task b2:forge:mcp` from the lab repo. That command starts the forge-cli MCP server, reads the seeded Snowflake schema, writes the raw logical model into `subscriber360-generated/runtime/generated/mcp-forge/`, and then generates:

- the hardened B2 `contract.fluid.yaml`
- dbt assets under `subscriber360-generated/generated/dbt/dbt_dv2_subscriber360`
- Airflow assets under `subscriber360-generated/generated/airflow`
- the Jenkins Pipeline-from-SCM file under `subscriber360-generated/Jenkinsfile`

The resulting silver product owns its generated assets inside the product folder. No B2 golden contract is copied.

See the variant playbook for the full command sequence.
