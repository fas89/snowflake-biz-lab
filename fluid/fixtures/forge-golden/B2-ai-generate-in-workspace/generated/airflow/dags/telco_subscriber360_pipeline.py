from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


with DAG(
    dag_id="telco_subscriber360_internal",
    start_date=datetime(2026, 1, 1),
    schedule="0 6 * * *",
    catchup=False,
    tags=["telco", "subscriber360", "reference"],
) as dag:
    validate_contract = BashOperator(
        task_id="validate_contract",
        bash_command="fluid validate variants/internal-reference/contract.fluid.yaml",
    )

    plan_contract = BashOperator(
        task_id="plan_contract",
        bash_command=(
            "fluid plan variants/internal-reference/contract.fluid.yaml "
            "--out variants/internal-reference/runtime/plan.json --html"
        ),
    )

    run_dbt = BashOperator(
        task_id="run_dbt_subscriber360",
        bash_command=(
            "dbt run --project-dir variants/internal-reference/dbt_dv2_subscriber360 "
            "--profiles-dir /workspace/config/dbt --profile telco "
            "--select mart_subscriber360_core mart_subscriber_health_scorecard"
        ),
    )

    publish_marketplace = BashOperator(
        task_id="publish_marketplace",
        bash_command="fluid publish variants/internal-reference/contract.fluid.yaml --catalog datamesh-manager",
    )

    validate_contract >> plan_contract >> run_dbt >> publish_marketplace
