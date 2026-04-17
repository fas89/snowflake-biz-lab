pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '20'))
  }

  parameters {
    booleanParam(
      name: 'RUN_SNOWFLAKE_TASKS',
      defaultValue: false,
      description: 'Run Snowflake-backed seed load, metadata apply, dbt run, and dbt test stages.'
    )
  }

  environment {
    DBT_PROFILES_DIR = 'config/dbt'
    DBT_PROJECT_DIR = 'dbt'
    PYTHONUNBUFFERED = '1'
  }

  stages {
    stage('Bootstrap') {
      steps {
        sh '''
          set -eu
          python3 --version
          dbt --version
        '''
      }
    }

    stage('Validate Seed Assets') {
      steps {
        sh '''
          set -eu
          python3 seed/generate_seed_data.py
          python3 seed/verify_seed_data.py --skip-snowflake
        '''
      }
    }

    stage('Validate Governance Manifest') {
      steps {
        sh '''
          set -eu
          python3 governance/render_metadata_sql.py --write
          python3 governance/verify_metadata.py --manifest-only
        '''
      }
    }

    stage('dbt Parse') {
      steps {
        sh '''
          set -eu
          dbt parse --project-dir "$DBT_PROJECT_DIR" --profiles-dir "$DBT_PROFILES_DIR" --profile telco
        '''
      }
    }

    stage('dbt Compile') {
      steps {
        sh '''
          set -eu
          dbt compile --project-dir "$DBT_PROJECT_DIR" --profiles-dir "$DBT_PROFILES_DIR" --profile telco
        '''
      }
    }

    stage('Snowflake Tasks') {
      when {
        expression {
          return params.RUN_SNOWFLAKE_TASKS &&
            env.SNOWFLAKE_ACCOUNT?.trim() &&
            env.SNOWFLAKE_USER?.trim() &&
            env.SNOWFLAKE_WAREHOUSE?.trim() &&
            env.SNOWFLAKE_DATABASE?.trim()
        }
      }
      stages {
        stage('Seed Load') {
          steps {
            sh '''
              set -eu
              python3 seed/load_to_snowflake.py
            '''
          }
        }

        stage('Apply Metadata') {
          steps {
            sh '''
              set -eu
              python3 governance/apply_metadata.py
            '''
          }
        }

        stage('dbt Run') {
          steps {
            sh '''
              set -eu
              dbt run --project-dir "$DBT_PROJECT_DIR" --profiles-dir "$DBT_PROFILES_DIR" --profile telco
            '''
          }
        }

        stage('dbt Test') {
          steps {
            sh '''
              set -eu
              dbt test --project-dir "$DBT_PROJECT_DIR" --profiles-dir "$DBT_PROFILES_DIR" --profile telco
            '''
          }
        }

        stage('Verify Metadata') {
          steps {
            sh '''
              set -eu
              python3 governance/verify_metadata.py
            '''
          }
        }
      }
    }

    stage('Snowflake Gate') {
      when {
        expression { return !params.RUN_SNOWFLAKE_TASKS }
      }
      steps {
        echo 'Snowflake-backed execution is disabled by default. Static repo validation completed without triggering Airflow.'
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'governance/sql/*.sql,runtime/**/*,seed/output/manifest.json,dbt/target/**/*', allowEmptyArchive: true
    }
  }
}

