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

copy_if_missing "$lab_repo/.env.example" "$lab_repo/.env"
copy_if_missing "$lab_repo/.env.catalogs.example" "$lab_repo/.env.catalogs"
copy_if_missing "$lab_repo/.env.jenkins.example" "$lab_repo/.env.jenkins"

python3 "$lab_repo/scripts/bootstrap_workspaces.py" --dest "$lab_repo/gitlab"

echo
echo "Local demo setup complete."
echo "LAB_REPO=$LAB_REPO"
echo "GREENFIELD_WORKSPACE=${GREENFIELD_WORKSPACE:-}"
echo "EXISTING_DBT_WORKSPACE=${EXISTING_DBT_WORKSPACE:-}"
