# Security Policy

## Supported Versions

The `main` branch is the supported community release line for this lab. Older
local demo branches and generated runtime outputs are not supported.

## Reporting A Vulnerability

Please do not open a public issue for an active vulnerability, exposed secret,
or exploitable misconfiguration.

Use GitHub private vulnerability reporting if it is enabled for this repository.
If private reporting is not available yet, contact the repository owner privately
through GitHub and ask for a secure disclosure channel.

Include:

- affected commit, file, or workflow
- short reproduction steps
- impact assessment
- whether any credential, token, or external account may be exposed

Please avoid including live secrets in the report. Redact tokens and share only
the minimum evidence needed to reproduce the issue.

## Demo Credential Guidance

This repository is a local demo lab. The default Airflow, Jenkins, Entropy, and
Postgres passwords are safe only with the default `LAB_BIND_ADDRESS=127.0.0.1`.
Before any shared or network-exposed demo, rotate the default local passwords and
use separate Snowflake, catalog, and API credentials from day-to-day accounts.
