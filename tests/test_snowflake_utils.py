from __future__ import annotations

import pytest

from config.snowflake_utils import (
    env_bool,
    execute_many,
    fq_name,
    get_env,
    quote_ident,
    sql_string,
)


class TestQuoteIdent:
    def test_wraps_in_double_quotes(self) -> None:
        assert quote_ident("FOO") == '"FOO"'

    def test_escapes_embedded_double_quote(self) -> None:
        assert quote_ident('WEIRD"NAME') == '"WEIRD""NAME"'

    def test_preserves_case_and_spaces(self) -> None:
        assert quote_ident("lower case") == '"lower case"'


class TestFqName:
    def test_joins_parts_with_dots(self) -> None:
        assert fq_name("DB", "SCHEMA", "TABLE") == '"DB"."SCHEMA"."TABLE"'

    def test_filters_empty_parts(self) -> None:
        assert fq_name("DB", "", "TABLE") == '"DB"."TABLE"'

    def test_escapes_each_part_independently(self) -> None:
        assert fq_name('A"B', "C") == '"A""B"."C"'


class TestSqlString:
    def test_wraps_in_single_quotes(self) -> None:
        assert sql_string("hello") == "'hello'"

    def test_doubles_embedded_single_quote(self) -> None:
        assert sql_string("O'Hara") == "'O''Hara'"

    def test_empty_string(self) -> None:
        assert sql_string("") == "''"


class TestGetEnv:
    def test_returns_set_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TEST_VAR_SET", "value")
        assert get_env("TEST_VAR_SET") == "value"

    def test_returns_default_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("TEST_VAR_UNSET", raising=False)
        assert get_env("TEST_VAR_UNSET", default="fallback") == "fallback"

    def test_returns_empty_string_when_unset_no_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("TEST_VAR_UNSET", raising=False)
        assert get_env("TEST_VAR_UNSET") == ""

    def test_required_raises_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("TEST_VAR_MISSING", raising=False)
        with pytest.raises(RuntimeError, match="Missing required environment variable"):
            get_env("TEST_VAR_MISSING", required=True)

    def test_required_raises_when_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TEST_VAR_EMPTY", "")
        with pytest.raises(RuntimeError):
            get_env("TEST_VAR_EMPTY", required=True)


class TestEnvBool:
    @pytest.mark.parametrize("value", ["1", "true", "True", "TRUE", "yes", "YES", "on", "On"])
    def test_truthy_values(self, value: str, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TEST_BOOL", value)
        assert env_bool("TEST_BOOL") is True

    @pytest.mark.parametrize("value", ["0", "false", "no", "off", "", "anything else"])
    def test_falsy_values(self, value: str, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TEST_BOOL", value)
        assert env_bool("TEST_BOOL") is False

    def test_default_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("TEST_BOOL_UNSET", raising=False)
        assert env_bool("TEST_BOOL_UNSET", default=True) is True
        assert env_bool("TEST_BOOL_UNSET", default=False) is False


class FakeCursor:
    def __init__(self) -> None:
        self.executed: list[str] = []

    def execute(self, sql: str) -> None:
        self.executed.append(sql)


class TestExecuteMany:
    def test_executes_each_non_empty_statement(self) -> None:
        cursor = FakeCursor()
        execute_many(cursor, ["SELECT 1", "SELECT 2"])
        assert cursor.executed == ["SELECT 1", "SELECT 2"]

    def test_skips_empty_and_whitespace_statements(self) -> None:
        cursor = FakeCursor()
        execute_many(cursor, ["SELECT 1", "", "   ", "\n", "SELECT 2"])
        assert cursor.executed == ["SELECT 1", "SELECT 2"]

    def test_strips_statement_whitespace(self) -> None:
        cursor = FakeCursor()
        execute_many(cursor, ["  SELECT 1  \n"])
        assert cursor.executed == ["SELECT 1"]
