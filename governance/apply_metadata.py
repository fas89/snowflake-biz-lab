from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config.snowflake_utils import env_bool, execute_many, get_connection  # noqa: E402
from governance.metadata_utils import (  # noqa: E402
    DEFAULT_MANIFEST_PATH,
    DEFAULT_SQL_PATH,
    load_manifest,
    render_sql_sections,
    write_sql_bundle,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply Snowflake Horizon metadata for seeded telco tables.")
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
    args = parser.parse_args()

    manifest = load_manifest(Path(args.manifest_path).resolve())
    sections = render_sql_sections(manifest)
    output_path = Path(args.output).resolve()
    write_sql_bundle(output_path, sections)

    enabled_sections = ["core", "schema", "tables"]
    if env_bool("SNOWFLAKE_ENABLE_CLASSIFICATION", False):
        enabled_sections.append("classification")
    if env_bool("SNOWFLAKE_ENABLE_DMF", False):
        enabled_sections.append("dmf")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            for section_name in enabled_sections:
                statements = sections[section_name]
                if not statements:
                    continue
                print(f"Applying {section_name} metadata ({len(statements)} statements)")
                execute_many(cursor, statements)

    print(f"Rendered metadata SQL written to {output_path}")


if __name__ == "__main__":
    main()

