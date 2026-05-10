FROM jenkins/jenkins:lts-jdk21

USER root
# git + curl for SCM checkout; build-essential + python3-dev for engine
# source builds. Python is provisioned by `uv` (next RUN) so we don't
# need the system python3* packages — Debian 13 ships Python 3.13 by
# default but several engine deps (airbyte 0.20.x → pyarrow / numpy)
# don't publish 3.13 wheels yet. Pinning to a known-good Python that
# the data ecosystem already supports (3.12) sidesteps the wheel gap.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git curl ca-certificates \
        build-essential \
        docker-cli \
        && \
    rm -rf /var/lib/apt/lists/*

# Engines that need /var/run/docker.sock at runtime are declared in
# forge-cli's engine-specs registry:
#
#   forge-cli/fluid_build/forge/core/pipeline_systems/_engine_specs.py
#     → resolve_engine_runtime(engine).needs_docker_socket
#
# Today: airbyte (PyAirbyte spawns source connectors as Docker images
# on the host's daemon), debezium / kafka_connect (when an operator
# chooses the side-car Connect cluster option). Pure-Python engines
# (dlt, meltano, dbt, duckdb) have ``needs_docker_socket=False`` —
# the chmod below is a no-op for them.
#
# docker-cli ships only the client, not a docker group — create one
# and add jenkins. The group GID matches whatever the kernel sees on
# the bound socket; on Docker Desktop macOS the socket is owned by
# root with mode 0660 so being in ANY non-root group AND having the
# right perms via sudoers would be needed — but Docker Desktop's
# macOS socket is actually 0660 root:root (no group restriction), so
# jenkins user just needs to be allowed to read it. We mode-relax
# the socket on the daemon side at compose time (see the volume mount).
RUN groupadd -f docker && usermod -aG docker jenkins

# Lab-only socket-perm relaxation: Docker Desktop on macOS bind-mounts
# /var/run/docker.sock as srw-rw---- root:root (mode 660). The jenkins
# user can't open it without matching the host's docker group GID,
# which differs by host. For lab simplicity, chmod the socket to 666
# at container-init via the wrapper ENTRYPOINT below. NEVER do this in
# production — granting docker socket access is root-equivalent.
#
# The chmod runs unconditionally because the lab Jenkins serves all
# engines from one image; fail-soft if no socket is mounted (pure-
# Python engines never use it). The "REQUIRES: docker.sock" line in
# generated Jenkinsfiles (from render_runtime_notes) tells operators
# which contracts need this bind-mount.
COPY <<'EOF' /usr/local/bin/lab-fix-docker-sock.sh
#!/bin/sh
set -e
# Container starts as root (the final USER directive at the bottom is
# intentionally NOT `USER jenkins` — we need root for the chmod). Then
# drop to jenkins for the actual Jenkins controller via runuser.
#
# Why runuser, not su:
#   `su -p jenkins` prompts for a password unless the caller is already
#   jenkins (PAM behavior). When the ENTRYPOINT inherited USER jenkins
#   from a previous image build, su silently switched to a password
#   prompt and the container exited with `Authentication failure`.
#   `runuser -u jenkins --` is the root-only counterpart: no PAM, no
#   password prompt, designed exactly for "root drops to a service
#   user before exec'ing the daemon" scenarios. Ships in util-linux
#   (already present in jenkins/jenkins:lts-jdk21).
if [ "$(id -u)" = "0" ]; then
  if [ -S /var/run/docker.sock ]; then
    chmod 666 /var/run/docker.sock 2>/dev/null || \
      echo "warn: could not chmod /var/run/docker.sock - PyAirbyte may fail" >&2
  fi
  # PyAirbyte's docker executor writes connector configs to
  # AIRBYTE_TEMP_DIR (defaults to /tmp/airbyte/tmp via the engine
  # specs registry). The /tmp/airbyte bind survives across container
  # restarts but the /tmp subdir gets wiped (host /tmp is volatile on
  # macOS/Linux reboots; Docker Desktop also wipes it on engine
  # restart). Recreating it here makes the lab self-healing.
  mkdir -p /tmp/airbyte/tmp 2>/dev/null && chmod 777 /tmp/airbyte/tmp 2>/dev/null || true
  # exec replaces this shell so jenkins.sh runs as PID 1's child.
  exec runuser -u jenkins -- /usr/local/bin/jenkins.sh "$@"
else
  # Not running as root (operator overrode `user:` in compose). Skip
  # the socket chmod (we couldn't if we tried) and just exec jenkins.sh
  # in-place. Engines that need the docker socket will hit a permission
  # error at exec time — the generated Jenkinsfile's REQUIRES line tells
  # the operator they need to run as root for those engines.
  exec /usr/local/bin/jenkins.sh "$@"
fi
EOF
RUN chmod +x /usr/local/bin/lab-fix-docker-sock.sh
# ENTRYPOINT runs as root (no USER override yet at container-start time);
# the script chmods then drops to jenkins via su. This is required so the
# bind-mounted Docker socket can be made jenkins-readable. Final USER at
# end of file controls who subsequent docker exec / cli commands run as.
ENTRYPOINT ["/usr/local/bin/lab-fix-docker-sock.sh"]
# All subsequent build steps (uv install, pip install, jenkins-plugin-cli)
# run as root because we never switch USER away. The ENTRYPOINT script
# above is what drops to jenkins via runuser at container start.

# Install ``uv`` (Astral) — a fast Python installer + version manager.
# We use it to fetch Python 3.12 (sidesteps Debian's 3.13 default), then
# create the canonical /opt/fluid-venv against that pinned interpreter.
# uv is a single static binary, no system-Python dependency.
ENV UV_PYTHON_INSTALL_DIR=/opt/uv-python
RUN curl -LsSf https://astral.sh/uv/install.sh -o /tmp/uv-install.sh && \
    UV_INSTALL_DIR=/usr/local/bin sh /tmp/uv-install.sh && \
    rm -f /tmp/uv-install.sh && \
    uv python install 3.12 && \
    uv venv --seed --python 3.12 /opt/fluid-venv && \
    /opt/fluid-venv/bin/python --version && \
    chmod -R o+rX /opt/uv-python

# Debian 13 enforces PEP 668: ``pip install`` against the system Python is
# blocked. We provision a dedicated venv at /opt/fluid-venv and prepend its
# bin to PATH so the generated Jenkinsfile's plain ``pip install`` and
# ``fluid …`` invocations target the venv. ``data-product-forge`` is
# pre-installed at image-build time so the per-build ``pip install`` is a
# fast no-op (and the demo still runs even if PyPI is unreachable).
ENV PATH="/opt/fluid-venv/bin:${PATH}"
# Install with [snowflake] extras so `fluid test` can run DQ rules against
# live Snowflake (snowflake-connector-python, snowpark, dbt-snowflake).
# Without this, `fluid test` trips on "snowflake-connector-python not
# installed" even for a Snowflake-bound contract.
RUN /opt/fluid-venv/bin/pip install --no-cache-dir --quiet --upgrade pip setuptools wheel && \
    /opt/fluid-venv/bin/pip install --no-cache-dir --quiet 'data-product-forge[snowflake]' && \
    chown -R jenkins:jenkins /opt/fluid-venv

COPY jenkins/plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

# NOTE: container intentionally runs as root at PID 1 (no final
# `USER jenkins` directive). The wrapper ENTRYPOINT chmods the
# bind-mounted Docker socket then `exec runuser -u jenkins --` the
# actual jenkins.sh. Switching back to USER jenkins here would make
# the ENTRYPOINT inherit jenkins, which can't chmod a root-owned
# socket and can't `runuser` (root-only). The Jenkins controller
# itself still runs as jenkins (via runuser), so workspace files
# get the right ownership.
