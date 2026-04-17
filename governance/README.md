# Governance

`metadata.yml` is the source of truth for Snowflake Horizon-facing metadata on the seeded telco landing tables.

The manifest is now intentionally maintained in two layers:

- hand-authored dataset, contact, tag, and important table overrides in `metadata.yml`
- safe auto-completion of missing table and column metadata in `metadata_utils.py`

That keeps the file friendly to maintain even as the telco model grows toward a broader SID-style shape.

This layer intentionally covers the metadata types that are practical to author from code in this repo:

- schema, table, and column comments
- user-defined tags on schemas, tables, and columns
- contacts for `ACCESS_APPROVAL`, `SECURITY_COMPLIANCE`, `STEWARD`, and `SUPPORT`
- sensitive-data classification hooks through `SYSTEM$CLASSIFY`
- data quality hooks through system data metric functions and expectations
- a draft Data Mesh Manager mapping skeleton for the Entropy-backed catalog stack

Key files:

- `metadata.yml`: hand-authored governance manifest
- `metadata_utils.py`: manifest loading, validation, auto-completion, and SQL rendering helpers
- `render_metadata_sql.py`: writes `governance/sql/rendered_metadata.sql`
- `apply_metadata.py`: renders and applies metadata to Snowflake
- `verify_metadata.py`: validates comments, tags, contacts, and DMF associations
- `datamesh_manager_mapping.yml`: draft catalog mapping for later DMM publication work

Notes:

- Classification and DMF features are gated by `SNOWFLAKE_ENABLE_CLASSIFICATION` and `SNOWFLAKE_ENABLE_DMF`.
- Comments and tag values are intentionally metadata-safe and do not contain regulated content.
- No catalog publish automation is configured in this phase.
