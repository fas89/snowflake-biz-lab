# B1 — AI Forge With External References

The operator runs `fluid init subscriber360-external --provider snowflake --yes` from this directory, then either:

- **Demo mode:** copies the captured golden contract from `fluid/fixtures/forge-golden/B1-ai-reference-external/contract.fluid.yaml` over `subscriber360-external/contract.fluid.yaml`
- **Live mode:** runs `fluid forge --provider snowflake --domain telco --target-dir .` which calls the real LLM

The resulting silver contract **references** external dbt and Airflow assets rather than generating them. Source-of-truth scripts for those external assets are in `path-a-telco-silver-product-demo/reference-assets/`.

See the variant playbook for the full command sequence.
