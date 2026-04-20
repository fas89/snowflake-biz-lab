FROM jenkins/jenkins:lts-jdk21

USER root
# python3-pip + python3-venv are required by the generated Jenkinsfile, which
# runs ``pip install --quiet data-product-forge`` in its Setup stage.
# python-is-python3 lets the generated scripts call ``python`` and ``pip``
# without the ``3`` suffix, matching the local-dev shell story.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 python3-pip python3-venv python-is-python3 git curl && \
    rm -rf /var/lib/apt/lists/*

# Debian 13 enforces PEP 668: ``pip install`` against the system Python is
# blocked. We provision a dedicated venv at /opt/fluid-venv and prepend its
# bin to PATH so the generated Jenkinsfile's plain ``pip install`` and
# ``fluid …`` invocations target the venv. ``data-product-forge`` is
# pre-installed at image-build time so the per-build ``pip install`` is a
# fast no-op (and the demo still runs even if PyPI is unreachable).
ENV PATH="/opt/fluid-venv/bin:${PATH}"
RUN python3 -m venv /opt/fluid-venv && \
    /opt/fluid-venv/bin/pip install --no-cache-dir --quiet --upgrade pip && \
    /opt/fluid-venv/bin/pip install --no-cache-dir --quiet data-product-forge && \
    chown -R jenkins:jenkins /opt/fluid-venv

COPY jenkins/plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

USER jenkins
