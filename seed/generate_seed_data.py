from __future__ import annotations

import argparse
from pathlib import Path

from telco_seed_data import write_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic telco seed CSV files.")
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parent / "output"),
        help="Directory where CSV files and manifest.json are written.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    manifest = write_dataset(output_dir)
    print(f"Generated {len(manifest['tables'])} seed files in {output_dir}")
    for table_name, table_meta in manifest["tables"].items():
        print(f"  {table_name}: {table_meta['row_count']} rows")


if __name__ == "__main__":
    main()
