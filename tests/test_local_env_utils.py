from __future__ import annotations

from pathlib import Path

from local_env_utils import parse_env_file, remove_env_keys, update_env_file


class TestParseEnvFile:
    def test_returns_empty_when_missing(self, tmp_path: Path) -> None:
        assert parse_env_file(tmp_path / "nonexistent.env") == {}

    def test_parses_simple_key_value_pairs(self, tmp_path: Path) -> None:
        path = tmp_path / "test.env"
        path.write_text("FOO=bar\nBAZ=qux\n")
        assert parse_env_file(path) == {"FOO": "bar", "BAZ": "qux"}

    def test_skips_comments_and_blank_lines(self, tmp_path: Path) -> None:
        path = tmp_path / "test.env"
        path.write_text("# header comment\n\nFOO=bar\n  # indented comment\nBAZ=qux\n")
        assert parse_env_file(path) == {"FOO": "bar", "BAZ": "qux"}

    def test_strips_surrounding_quotes(self, tmp_path: Path) -> None:
        path = tmp_path / "test.env"
        path.write_text("FOO='quoted'\nBAR=\"double\"\nBAZ=plain\n")
        assert parse_env_file(path) == {"FOO": "quoted", "BAR": "double", "BAZ": "plain"}

    def test_preserves_equals_in_value(self, tmp_path: Path) -> None:
        path = tmp_path / "test.env"
        path.write_text("TOKEN=abc=def=ghi\n")
        assert parse_env_file(path) == {"TOKEN": "abc=def=ghi"}

    def test_ignores_lines_without_equals(self, tmp_path: Path) -> None:
        path = tmp_path / "test.env"
        path.write_text("FOO=bar\nNOT_A_KEY_VALUE_LINE\n")
        assert parse_env_file(path) == {"FOO": "bar"}


class TestUpdateEnvFile:
    def test_creates_file_with_new_keys(self, tmp_path: Path) -> None:
        path = tmp_path / "new.env"
        update_env_file(path, {"FOO": "bar"})
        assert path.read_text() == "FOO=bar\n"

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        path = tmp_path / "nested" / "dir" / "new.env"
        update_env_file(path, {"FOO": "bar"})
        assert path.exists()
        assert path.read_text() == "FOO=bar\n"

    def test_updates_existing_key_in_place(self, tmp_path: Path) -> None:
        path = tmp_path / "test.env"
        path.write_text("FOO=old\nBAR=keep\n")
        update_env_file(path, {"FOO": "new"})
        assert parse_env_file(path) == {"FOO": "new", "BAR": "keep"}

    def test_appends_new_keys_at_end(self, tmp_path: Path) -> None:
        path = tmp_path / "test.env"
        path.write_text("FOO=1\n")
        update_env_file(path, {"BAR": "2"})
        lines = path.read_text().splitlines()
        assert lines == ["FOO=1", "BAR=2"]

    def test_preserves_comments_and_blank_lines(self, tmp_path: Path) -> None:
        path = tmp_path / "test.env"
        path.write_text("# top comment\n\nFOO=1\n# mid comment\nBAR=2\n")
        update_env_file(path, {"FOO": "NEW"})
        content = path.read_text()
        assert "# top comment" in content
        assert "# mid comment" in content
        assert "FOO=NEW" in content


class TestRemoveEnvKeys:
    def test_noop_when_file_missing(self, tmp_path: Path) -> None:
        remove_env_keys(tmp_path / "missing.env", {"FOO"})

    def test_removes_targeted_keys(self, tmp_path: Path) -> None:
        path = tmp_path / "test.env"
        path.write_text("FOO=1\nBAR=2\nBAZ=3\n")
        remove_env_keys(path, {"BAR"})
        assert parse_env_file(path) == {"FOO": "1", "BAZ": "3"}

    def test_preserves_comments(self, tmp_path: Path) -> None:
        path = tmp_path / "test.env"
        path.write_text("# keep me\nFOO=1\nBAR=2\n")
        remove_env_keys(path, {"FOO"})
        assert "# keep me" in path.read_text()

    def test_removing_missing_key_is_noop(self, tmp_path: Path) -> None:
        path = tmp_path / "test.env"
        path.write_text("FOO=1\n")
        remove_env_keys(path, {"NOT_PRESENT"})
        assert parse_env_file(path) == {"FOO": "1"}
