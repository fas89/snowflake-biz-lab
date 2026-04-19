#!/bin/sh

set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
lab_repo=$(CDPATH= cd -- "$script_dir/.." && pwd)
launchpad_file="$lab_repo/runtime/generated/launchpad.local.sh"

force=0
local_repos_dir=""

for arg in "$@"; do
  case "$arg" in
    --force)
      force=1
      ;;
    *)
      if [ -z "$local_repos_dir" ]; then
        local_repos_dir="$arg"
      else
        echo "Usage: ./scripts/setup_mac_launchpad.sh [LOCAL_REPOS_DIR] [--force]" >&2
        exit 1
      fi
      ;;
  esac
done

if [ -z "$local_repos_dir" ]; then
  local_repos_dir=$(CDPATH= cd -- "$lab_repo/.." && pwd)
fi

# Derive the default path layout from the chosen parent repo folder instead of
# inheriting possibly stale shell variables from a previous demo run.
demo_workspaces_dir="$local_repos_dir/gitlab"
greenfield_workspace="$demo_workspaces_dir/telco-silver-product-demo"
existing_dbt_workspace="$demo_workspaces_dir/telco-silver-import-demo"
greenfield_gitlab_url=""
existing_dbt_gitlab_url=""
fluid_secrets_file="$lab_repo/runtime/generated/fluid.local.env"
forge_cli_repo="$local_repos_dir/forge-cli"

quote_for_shell() {
  escaped=$(printf "%s" "$1" | sed "s/'/'\\\\''/g")
  printf "'%s'" "$escaped"
}

mkdir -p "$lab_repo/runtime/generated" "$demo_workspaces_dir"

if [ -e "$launchpad_file" ] && [ "$force" -ne 1 ]; then
  echo "Keeping existing launchpad file: $launchpad_file"
  echo "This is normal if you already set up your local paths."
  echo "Use --force only when you want to regenerate it."
  echo
  echo "Next step:"
  echo "  source runtime/generated/launchpad.local.sh"
  exit 0
fi

cat > "$launchpad_file" <<EOF
export LOCAL_REPOS_DIR=$(quote_for_shell "$local_repos_dir") # parent folder that holds snowflake-biz-lab and forge-cli
export LAB_REPO=$(quote_for_shell "$lab_repo") # local clone of this repo
export FORGE_CLI_REPO=$(quote_for_shell "$forge_cli_repo") # editable forge-cli checkout or worktree
export DEMO_WORKSPACES_DIR=$(quote_for_shell "$demo_workspaces_dir") # parent folder for the GitLab demo workspaces
export GREENFIELD_WORKSPACE=$(quote_for_shell "$greenfield_workspace") # GitLab working copy for the main demo
export EXISTING_DBT_WORKSPACE=$(quote_for_shell "$existing_dbt_workspace") # GitLab working copy for the existing-dbt variation
export GREENFIELD_GITLAB_URL=$(quote_for_shell "$greenfield_gitlab_url") # Git clone URL for the main demo workspace
export EXISTING_DBT_GITLAB_URL=$(quote_for_shell "$existing_dbt_gitlab_url") # Git clone URL for the existing-dbt demo workspace
export FLUID_SECRETS_FILE=$(quote_for_shell "$fluid_secrets_file") # ignored file that holds Snowflake and DMM secrets
EOF

echo "Created $launchpad_file"
echo
echo "Detected values:"
echo "  LOCAL_REPOS_DIR=$local_repos_dir"
echo "  LAB_REPO=$lab_repo"
echo "  FORGE_CLI_REPO=$forge_cli_repo"
echo "  DEMO_WORKSPACES_DIR=$demo_workspaces_dir"
echo
echo "Next steps:"
echo "  1. Review the generated file if you want to override any paths."
echo "  2. Set GREENFIELD_GITLAB_URL and EXISTING_DBT_GITLAB_URL in runtime/generated/launchpad.local.sh before running any git clone commands."
echo "     If you already cloned those workspaces manually, you can leave the URL values empty and skip the git clone step."
echo "  3. Load it into your shell to refresh the current path variables:"
echo "     source runtime/generated/launchpad.local.sh"
echo "  4. Continue with docs/launchpad-common.md"
