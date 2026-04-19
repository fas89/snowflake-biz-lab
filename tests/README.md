# Tests

Minimal pytest harness covering pure-function modules that are imported across the project.

## What's covered

- `config/snowflake_utils.py` — identifier/literal quoting (`quote_ident`, `fq_name`, `sql_string`), env-var helpers (`get_env`, `env_bool`), cursor execution (`execute_many`).
- `scripts/local_env_utils.py` — `.env` file round-trip (`parse_env_file`, `update_env_file`, `remove_env_keys`).

## What's not covered (yet)

These modules hit live Snowflake, HTTP, or generate large synthetic datasets — they need fixtures or mocks and are out of scope for the initial harness:

- `seed/telco_seed_data.py` — deterministic-seed regression tests would be valuable.
- `governance/metadata_utils.py` — YAML manifest validation branches.
- `scripts/bootstrap_entropy_local.py` — HTTP state machine; needs `urllib` mocking.
- `seed/load_to_snowflake.py` — Snowflake PUT/COPY integration; needs a connector mock or an integration-test tier.

## Running

From the repo root:

```sh
python3 -m pytest tests/
```

Or with a specific venv:

```sh
.venv.fluid-dev/bin/python -m pytest tests/
```

These tests have no external dependencies (no network, no Snowflake, no Docker).
