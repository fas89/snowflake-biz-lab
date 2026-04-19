from __future__ import annotations

import argparse
from pathlib import Path

from config.snowflake_utils import execute_many, get_connection
from governance.metadata_utils import (
    DEFAULT_MANIFEST_PATH,
    DEFAULT_SQL_PATH,
    load_manifest,
    render_sql_sections,
    write_sql_bundle,
)


def _filter_comment_sections(sections: dict[str, list[str]]) -> dict[str, list[str]]:
    return {
        "schema_comments": [
            statement
            for statement in sections["schema"]
            if statement.strip().upper().startswith("COMMENT ON SCHEMA")
        ],
        "table_comments": [
            statement
            for statement in sections["tables"]
            if statement.strip().upper().startswith("COMMENT ON TABLE")
            or statement.strip().upper().startswith("COMMENT ON COLUMN")
        ],
    }


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
    sections = _filter_comment_sections(render_sql_sections(manifest))
    output_path = Path(args.output).resolve()
    write_sql_bundle(output_path, sections)

    with get_connection() as conn:
        with conn.cursor() as cursor:
            for section_name, statements in sections.items():
                if not statements:
                    continue
                print(f"Applying {section_name} metadata ({len(statements)} statements)")
                execute_many(cursor, statements)

    print(f"Rendered metadata SQL written to {output_path}")


if __name__ == "__main__":
    main()
