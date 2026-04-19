from __future__ import annotations

import argparse
from pathlib import Path

from local_env_utils import remove_env_keys


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove locally generated Entropy credentials so the catalog stack can be bootstrapped from scratch."
    )
    parser.add_argument(
        "--fluid-secrets-file",
        required=True,
        help="Path to runtime/generated/fluid.local.env or another local FLUID secrets file.",
    )
    args = parser.parse_args()

    fluid_secrets_file = Path(args.fluid_secrets_file).expanduser().resolve()
    remove_env_keys(fluid_secrets_file, {"DMM_API_KEY"})
    print(f"Removed DMM_API_KEY from {fluid_secrets_file}")


if __name__ == "__main__":
    main()
