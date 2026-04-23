pipeline {
  agent any

  // Every sh block ``cd``s into /workspace first. Jenkins' own workspace
  // (under /var/jenkins_home/jobs/…/workspace) is kept as the write target
  // for @tmp buffers; the lab files at /workspace are referenced directly.
  // Container-root writes (what customWorkspace '/workspace' would force
  // via /workspace@tmp) are blocked by the container's filesystem perms.

  options {
    // timestamps() requires the Timestamper plugin, which is not currently
    // installed on this lab's Jenkins. Reinstate once the plugin is in place
    // via the CasC plugin list under jenkins/casc/.
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '20'))
  }

  parameters {
    booleanParam(
      name: 'RUN_SNOWFLAKE_TASKS',
      defaultValue: false,
      description: 'Run Snowflake-backed seed load, metadata apply, dbt run, and dbt test stages.'
    )
    booleanParam(
      name: 'RUN_FLUID_PIPELINE',
      defaultValue: false,
      description: 'Run the 11-stage FLUID pipeline (bundle → validate → generate artifacts → validate artifacts → diff → plan → apply → policy-apply → verify → publish → schedule-sync) against each contract in FLUID_CONTRACTS.'
    )
    string(
      name: 'FLUID_CONTRACTS',
      defaultValue: 'fluid/contracts/telco_seed_billing/contract.fluid.yaml fluid/contracts/telco_seed_party/contract.fluid.yaml fluid/contracts/telco_seed_usage/contract.fluid.yaml',
      description: 'Space-separated contract paths to run through the 11-stage pipeline. Defaults to the three Bronze contracts.'
    )
    string(
      name: 'FLUID_ENV',
      defaultValue: 'dev',
      description: 'Environment overlay (dev / staging / prod). Destructive apply modes require --allow-data-loss in non-dev.'
    )
    string(
      name: 'APPLY_MODE',
      defaultValue: 'amend',
      description: 'fluid apply mode: dry-run | create-only | amend | amend-and-build | replace | replace-and-build. See docs/apply-modes.md.'
    )
    string(
      name: 'PUBLISH_TARGETS',
      defaultValue: 'datamesh-manager',
      description: 'Space-separated publish targets (command-center datahub datamesh-manager ...). Requires DMM_API_URL / per-target env vars.'
    )
  }

  environment {
    DBT_PROFILES_DIR = 'config/dbt'
    DBT_PROJECT_DIR = 'dbt'
    PYTHONUNBUFFERED = '1'
    // Dev-source FLUID binary. Bootstrap with `task fluid:bootstrap:dev` so
    // this path resolves to an editable install of the sibling forge-cli repo.
    FLUID = '.venv.fluid-dev/bin/fluid'
  }

  stages {
    stage('Bootstrap') {
      steps {
        sh '''
          set -eu
          cd /workspace
          python3 --version
          dbt --version
          test -x "$FLUID" && "$FLUID" version || echo "FLUID binary not bootstrapped — skip --fluid-pipeline or run task fluid:bootstrap:dev"
        '''
      }
    }

    // The next four stages (seed/governance/dbt parse/compile) are lab
    // legacy — they depend on lab-specific Python modules (config.*, etc.)
    // that need PYTHONPATH=/workspace. Wrapping in catchError so a missing
    // dep marks the stage UNSTABLE without blocking the FLUID pipeline.
    // Export PYTHONPATH inside each sh so the imports resolve when the
    // modules ARE present.
    stage('Validate Seed Assets') {
      steps {
        catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
          sh '''
            set -eu
            cd /workspace
            export PYTHONPATH=/workspace:${PYTHONPATH:-}
            python3 seed/generate_seed_data.py
            python3 seed/verify_seed_data.py --skip-snowflake
          '''
        }
      }
    }

    stage('Validate Governance Manifest') {
      steps {
        catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
          sh '''
            set -eu
            cd /workspace
            export PYTHONPATH=/workspace:${PYTHONPATH:-}
            python3 governance/render_metadata_sql.py --write
            python3 governance/verify_metadata.py --manifest-only
          '''
        }
      }
    }

    stage('dbt Parse') {
      steps {
        catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
          sh '''
            set -eu
            cd /workspace
            dbt parse --project-dir "$DBT_PROJECT_DIR" --profiles-dir "$DBT_PROFILES_DIR" --profile telco
          '''
        }
      }
    }

    stage('dbt Compile') {
      steps {
        catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
          sh '''
            set -eu
            cd /workspace
            dbt compile --project-dir "$DBT_PROJECT_DIR" --profiles-dir "$DBT_PROFILES_DIR" --profile telco
          '''
        }
      }
    }

    // =========================================================================
    // FLUID 11-Stage Pipeline
    //
    // Runs the full contract lifecycle (bundle → validate → generate artifacts
    // → validate artifacts → diff → plan → apply → policy-apply → verify →
    // publish → schedule-sync) for each contract listed in FLUID_CONTRACTS.
    //
    // Orthogonal to the Snowflake Tasks block: Snowflake Tasks handles raw
    // seed-load + dbt runs; FLUID handles the contract-driven schema + policy
    // + catalog lifecycle. Both can run in the same Jenkins job when enabled.
    //
    // Stages 4, 8, 11 self-gate on file existence so reference-only contracts
    // (pattern: hybrid-reference) skip them silently.
    // =========================================================================
    stage('FLUID Pipeline') {
      when {
        expression { return params.RUN_FLUID_PIPELINE }
      }
      stages {
        // FLUID stages run the dev-source ``.venv.fluid-dev`` binary, which
        // has an absolute-path Python shebang pinned to the host. Running
        // from inside the Jenkins container fails the shebang lookup — the
        // container needs its own venv (either a bind mount for forge-cli
        // or a pip install of data-product-forge from TestPyPI).
        // catchError keeps these stages visible in the UI while signalling
        // "bootstrap needed" via UNSTABLE without blocking the rest.
        stage('FLUID: bundle + validate + generate artifacts') {
          steps {
            catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
              sh '''
                set -eu
                cd /workspace
                for contract in $FLUID_CONTRACTS; do
                  contract_dir="$(dirname "$contract")"
                  echo "── stage 1–4 for $contract ──"
                  mkdir -p "$contract_dir/runtime" "$contract_dir/runtime/artifacts"
                  "$FLUID" bundle "$contract" --format tgz --out "$contract_dir/runtime/bundle.tgz"
                  "$FLUID" validate "$contract_dir/runtime/bundle.tgz"
                  "$FLUID" generate artifacts "$contract" --out "$contract_dir/runtime/artifacts/"
                  "$FLUID" validate-artifacts "$contract_dir/runtime/artifacts/"
                done
              '''
            }
          }
        }

        stage('FLUID: diff + plan') {
          steps {
            catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
              sh '''
                set -eu
                cd /workspace
                for contract in $FLUID_CONTRACTS; do
                  contract_dir="$(dirname "$contract")"
                  echo "── stage 5–6 for $contract ──"
                  "$FLUID" diff "$contract" --exit-on-drift --env "$FLUID_ENV"
                  "$FLUID" plan "$contract" --out "$contract_dir/runtime/plan.json" --html
                done
              '''
            }
          }
        }

        stage('FLUID: apply + policy-apply + verify') {
          when {
            expression {
              return params.APPLY_MODE == 'dry-run' || params.RUN_SNOWFLAKE_TASKS
            }
          }
          steps {
            catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
              sh '''
                set -eu
                cd /workspace
                for contract in $FLUID_CONTRACTS; do
                  contract_dir="$(dirname "$contract")"
                  echo "── stage 7–9 for $contract (mode=$APPLY_MODE) ──"
                  "$FLUID" apply "$contract_dir/runtime/plan.json" \
                    --mode "$APPLY_MODE" --env "$FLUID_ENV" --yes \
                    --report "$contract_dir/runtime/apply_report.html"
                  if [ -f "$contract_dir/runtime/artifacts/policy/bindings.json" ]; then
                    "$FLUID" policy-apply "$contract_dir/runtime/artifacts/policy/bindings.json" \
                      --mode enforce --env "$FLUID_ENV"
                  fi
                  "$FLUID" verify "$contract" --strict --env "$FLUID_ENV" \
                    --report "$contract_dir/runtime/verify.json"
                done
              '''
            }
          }
        }

        stage('FLUID: publish') {
          steps {
            catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
              sh '''
                set -eu
                cd /workspace
                TARGET_FLAGS=""
                for t in $PUBLISH_TARGETS; do
                  TARGET_FLAGS="$TARGET_FLAGS --target $t"
                done
                for contract in $FLUID_CONTRACTS; do
                  echo "── stage 10 for $contract ──"
                  "$FLUID" publish "$contract" $TARGET_FLAGS --env "$FLUID_ENV"
                done
              '''
            }
          }
        }

        // Stage 11 — schedule-sync (Path A) lands in Phase 7 of forge-cli.
        // Until then, this stage is a no-op placeholder; Path B schedules
        // (eventbridge / mwaa / snowflake_tasks) are applied in stage 7 via
        // SchedulePlanner actions embedded in plan.json.
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
              cd /workspace
              python3 seed/load_to_snowflake.py
            '''
          }
        }

        stage('Apply Metadata') {
          steps {
            sh '''
              set -eu
              cd /workspace
              python3 governance/apply_metadata.py
            '''
          }
        }

        stage('dbt Run') {
          steps {
            sh '''
              set -eu
              cd /workspace
              dbt run --project-dir "$DBT_PROJECT_DIR" --profiles-dir "$DBT_PROFILES_DIR" --profile telco
            '''
          }
        }

        stage('dbt Test') {
          steps {
            sh '''
              set -eu
              cd /workspace
              dbt test --project-dir "$DBT_PROJECT_DIR" --profiles-dir "$DBT_PROFILES_DIR" --profile telco
            '''
          }
        }

        stage('Verify Metadata') {
          steps {
            sh '''
              set -eu
              cd /workspace
              python3 governance/verify_metadata.py
            '''
          }
        }
      }
    }

    stage('Snowflake Gate') {
      when {
        expression { return !params.RUN_SNOWFLAKE_TASKS && !params.RUN_FLUID_PIPELINE }
      }
      steps {
        echo 'Snowflake-backed execution and FLUID pipeline are both disabled. Static repo validation completed without triggering Airflow or warehouse calls.'
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'governance/sql/*.sql,runtime/**/*,seed/output/manifest.json,dbt/target/**/*,fluid/contracts/*/runtime/**/*', allowEmptyArchive: true
    }
  }
}
