# B2 — AI Forge With Generated Assets

The operator runs `fluid init subscriber360-generated --provider snowflake --yes` from this directory, then either:

- **Demo mode:** copies the captured golden contract from `fluid/fixtures/forge-golden/B2-ai-generate-in-workspace/contract.fluid.yaml` over `subscriber360-generated/contract.fluid.yaml`
- **Live mode:** runs `fluid forge --provider snowflake --domain telco --target-dir .` which calls the real LLM

After the contract exists, `fluid generate transformation` produces dbt and `fluid generate schedule` produces Airflow into the same workspace (no external references).

See the variant playbook for the full command sequence.
