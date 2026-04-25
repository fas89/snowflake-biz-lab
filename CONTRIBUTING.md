# Contributing

Thanks for helping improve Snowflake Telco Lab.

## Development Setup

Use Python 3.10 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest -q
```

The Docker launchpads use local `.env` files and generated runtime state. Keep
those files untracked.

## Security And Secrets

Never commit:

- `.env`, `.env.catalogs`, or `.env.jenkins`
- `runtime/generated/fluid.local.env`
- generated plan screenshots or reports that contain credentials
- Snowflake passwords, private keys, OAuth tokens, DMM API keys, or cloud API keys

The local demo defaults bind services to `127.0.0.1`. If you expose the lab to a
network, rotate the demo passwords first.

## Pull Request Checklist

Before opening a pull request:

- run `python -m pytest -q`
- run `docker compose --env-file .env.example -f deploy/docker/docker-compose.yml config`
- run `docker compose --env-file .env.catalogs.example -f deploy/docker/catalogs/docker-compose.catalogs.yml config`
- confirm no generated runtime files are included
- update docs when changing launchpad commands or local service behavior

## Licensing

By contributing, you agree that your contribution is licensed under the Apache
License, Version 2.0.
