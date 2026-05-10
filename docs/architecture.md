# Architecture Notes

- Snowflake is the only warehouse target in this repo.
- `seed/` owns raw file generation and landing-table loads.
- `dbt/` owns cleaned staging views or tables in `SNOWFLAKE_DBT_SCHEMA`.
- `fluid/` now owns FLUID contracts, demo runbooks, track checks, and future contract-adjacent assets.
- `governance/` owns comments, tags, contacts, classification hooks, and DMF hooks.
- `runtime/generated/` is the local-only home for ignored FLUID/Snowflake credential files.
- `runtime/wheels/` is reserved for backup demo install artifacts.
- `airflow/` is intentionally scaffold-only in this phase. The stack is present, but no DAG code is checked in yet.
- `jenkins/` provides CI bootstrap and Snowflake-gated validation without orchestrating Airflow.
- Hosted GitLab is the intended contract system of record later, but no `.gitlab-ci.yml` or FLUID CI generation is added in this phase.

## Jenkins Container — Privilege Model

The lab Jenkins container (`deploy/docker/jenkins/Dockerfile`) is intentionally root-at-PID-1, drops to the `jenkins` user via `runuser` for the controller process, and chmods the bind-mounted Docker socket to `666` at startup. This is **lab-only convenience** and would be a serious privilege escalation in a shared / production controller — every comment in the Dockerfile and `docker-compose.yml` says "NEVER do this in production".

### Why root at PID 1

1. The wrapper ENTRYPOINT (`/usr/local/bin/lab-fix-docker-sock.sh`) needs to `chmod 666 /var/run/docker.sock` so the `jenkins` user can talk to the host's Docker daemon. PyAirbyte (used by pre-2) spawns each source connector as a sibling Docker container via the bound socket; without the chmod, the spawn fails with "Connector executable not found".
2. The same script needs to `mkdir -p /tmp/airbyte/tmp` on every container start. The bind mount survives restarts but the host's `/tmp` subdir gets wiped on macOS reboot or a Docker Desktop engine restart, so re-creating it on boot makes the lab self-healing.
3. Once chmod and mkdir are done, the script `exec runuser -u jenkins -- /usr/local/bin/jenkins.sh "$@"` so the Jenkins controller (Java process) actually runs as `jenkins` and workspace files get the right ownership.

### Why `runuser`, not `su`

`su -p jenkins` invokes PAM, which prompts for a password unless the caller is already `jenkins`. With root-at-PID-1 the caller IS root but PAM's behavior in container ENTRYPOINTs makes the script appear interactive and the container exits with `Authentication failure`. `runuser -u jenkins --` is the root-only equivalent: no PAM, no password prompt. It ships in `util-linux`, pre-installed in `jenkins/jenkins:lts-jdk21`.

### Defense-in-depth

The wrapper script also handles the non-root case: if an operator overrides `user:` in the compose file, the script skips the chmod and `exec`s `jenkins.sh` in place. Engines that need the Docker socket then surface the requirement at exec time, and the generated Jenkinsfile's `REQUIRES: docker.sock` comment (emitted by forge-cli's `render_runtime_notes()`) tells the operator what mount they need.

## DinD Volume Sharing for PyAirbyte

PyAirbyte's docker executor mounts `tempfile.gettempdir()` (default `/tmp`) into the spawned source-connector container at `/airbyte/tmp`. With Docker-in-Docker (the Jenkins container talking to the host's Docker daemon), the daemon resolves volume paths against the **host filesystem** — it has no view of the runner container's bind translations. So the path the runner writes to and the path the daemon mounts must be **identical absolute paths on host and runner**.

Two mechanisms make this work in the lab:

1. `deploy/docker/docker-compose.yml` bind-mounts `/tmp/airbyte:/tmp/airbyte` symmetrically — same path both sides.
2. The forge-cli engine specs registry emits two env vars into the generated Jenkinsfile for `engine='airbyte'`:
   - `AIRBYTE_PROJECT_DIR=/tmp/airbyte` — PyAirbyte caches `Path.cwd()` at module-import time and reuses it for connector mount dirs; CI runners typically import from `/` (root) which would make `/<connector-name>` unwritable.
   - `AIRBYTE_TEMP_DIR=/tmp/airbyte/tmp` — overrides PyAirbyte's `tempfile.NamedTemporaryFile(dir=...)` call so the connector config JSON lands in the bind-mounted dir, where the host docker daemon can find it via the symmetric path.

Without either mechanism, the spawned connector dies with `NoSuchFileException: /airbyte/tmp/tmpXXX.json` because the host's `/tmp/airbyte/tmp` is empty (the temp file lived in the runner container's `/tmp`). See [Troubleshooting](troubleshooting.md) for the exact failure-mode entries.

## FLUID Runner Loopback Override

Contracts often declare source connections as `host: localhost` (correct from the contract author's perspective on their dev machine). When the FLUID acquisition runner (dlt / PyAirbyte / Meltano source adapter) executes inside a Jenkins container, `localhost` resolves to the container itself, not the host's Postgres at port 5433.

The lab solves this with `FLUID_RUNNER_HOST_OVERRIDE=host.docker.internal` (Docker Desktop) — emitted into the generated Jenkinsfile's `environment {}` block by `fluid generate ci --runner-host-override host.docker.internal`. The acquisition runners read it and rewrite contract-author `localhost` → `host.docker.internal` at exec time. Linux Docker setups would set this to the bridge IP; Kubernetes setups would set it to a Service name.
