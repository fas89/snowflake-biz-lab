#!/bin/sh

set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
lab_repo=$(CDPATH= cd -- "$script_dir/.." && pwd)
launchpad_file="$lab_repo/runtime/generated/launchpad.local.sh"

if [ ! -f "$launchpad_file" ]; then
  echo "Missing $launchpad_file" >&2
  echo "Run ./scripts/setup_mac_launchpad.sh first." >&2
  exit 1
fi

# shellcheck source=/dev/null
. "$launchpad_file"

copy_if_missing() {
  src="$1"
  dest="$2"
  if [ -f "$dest" ]; then
    echo "Keeping existing $(basename "$dest")"
  else
    cp "$src" "$dest"
    echo "Created $(basename "$dest")"
  fi
}

clone_if_configured() {
  repo_url="$1"
  target_dir="$2"
  label="$3"

  mkdir -p "$(dirname "$target_dir")"

  if [ -z "$repo_url" ]; then
    mkdir -p "$target_dir"
    echo "Skipping $label clone because its GitLab URL is empty."
    echo "Created or kept local folder: $target_dir"
    echo "Set the URL in runtime/generated/launchpad.local.sh if you want this script to clone it."
    return 0
  fi

  if [ -d "$target_dir/.git" ]; then
    echo "Keeping existing $label workspace at $target_dir"
    return 0
  fi

  if [ -d "$target_dir" ] && [ -n "$(ls -A "$target_dir" 2>/dev/null)" ]; then
    echo "Skipping $label clone because $target_dir already exists and is not empty."
    echo "Either remove that folder or clone the repo there yourself."
    return 0
  fi

  if [ -d "$target_dir" ] && [ -z "$(ls -A "$target_dir" 2>/dev/null)" ]; then
    rmdir "$target_dir"
  fi

  git clone "$repo_url" "$target_dir"
}

copy_if_missing "$lab_repo/.env.example" "$lab_repo/.env"
copy_if_missing "$lab_repo/.env.catalogs.example" "$lab_repo/.env.catalogs"
copy_if_missing "$lab_repo/.env.jenkins.example" "$lab_repo/.env.jenkins"

clone_if_configured "${GREENFIELD_GITLAB_URL:-}" "${GREENFIELD_WORKSPACE:-}" "greenfield"
clone_if_configured "${EXISTING_DBT_GITLAB_URL:-}" "${EXISTING_DBT_WORKSPACE:-}" "existing-dbt"

echo
echo "Local demo setup complete."
echo "LAB_REPO=$LAB_REPO"
echo "GREENFIELD_WORKSPACE=${GREENFIELD_WORKSPACE:-}"
echo "EXISTING_DBT_WORKSPACE=${EXISTING_DBT_WORKSPACE:-}"
