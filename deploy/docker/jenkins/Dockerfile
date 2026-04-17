FROM jenkins/jenkins:lts-jdk21

USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip git curl && \
    rm -rf /var/lib/apt/lists/*

COPY jenkins/plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

RUN pip3 install --no-cache-dir \
    "dbt-core==1.8.2" \
    "dbt-snowflake==1.8.2" \
    "pyyaml>=6.0" \
    "snowflake-connector-python>=3.12,<4.0"

USER jenkins
