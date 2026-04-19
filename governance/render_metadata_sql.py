from __future__ import annotations

import argparse
from pathlib import Path

from governance.metadata_utils import (
    DEFAULT_MANIFEST_PATH,
    DEFAULT_SQL_PATH,
    load_manifest,
    render_sql_sections,
    write_sql_bundle,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render Snowflake Horizon metadata SQL from metadata.yml.")
    parser.add_argument(
        "--manifest-path",
        default=str(DEFAULT_MANIFEST_PATH),
        help="Path to the governance metadata manifest.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_SQL_PATH),
        help="Path to the rendered SQL bundle.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write the rendered SQL bundle to disk.",
    )
    args = parser.parse_args()

    manifest = load_manifest(Path(args.manifest_path).resolve())
    sections = render_sql_sections(manifest)

    if args.write:
        output_path = Path(args.output).resolve()
        write_sql_bundle(output_path, sections)
        print(f"Wrote rendered metadata SQL to {output_path}")
    else:
        for section_name, statements in sections.items():
            print(f"-- {section_name}")
            for statement in statements:
                print(statement + ";")
            print()


if __name__ == "__main__":
    main()
