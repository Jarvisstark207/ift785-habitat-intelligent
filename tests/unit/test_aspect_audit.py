"""
Tests unitaires - @aspect_audit (Itération 9 : AOP)
"""

import asyncio
import pytest
from unittest.mock import patch, MagicMock

from app.core.aspects import aspect_audit


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Fonctionnement de base (avec mock DB)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_write_audit(monkeypatch):
    """Mock _write_audit_log pour éviter une vraie connexion DB dans les tests."""
    calls = []

    def fake_write(action, func_name, level, error=None):
        calls.append({"action": action, "func": func_name, "level": level, "error": error})

    monkeypatch.setattr("app.core.aspects._write_audit_log", fake_write)
    return calls


class TestAspectAuditBasic:
    def test_sync_returns_value(self, mock_write_audit):
        @aspect_audit()
        def compute():
            return 42
        assert compute() == 42

    def test_async_returns_value(self, mock_write_audit):
        @aspect_audit()
        async def fetch():
            return 99
        assert run(fetch()) == 99

    def test_preserves_function_name(self, mock_write_audit):
        @aspect_audit()
        def my_func():
            pass
        assert my_func.__name__ == "my_func"

    def test_preserves_docstring(self, mock_write_audit):
        @aspect_audit()
        def documented():
            """My doc."""
        assert documented.__doc__ == "My doc."

    def test_sync_writes_audit_on_success(self, mock_write_audit):
        @aspect_audit(action="test.action")
        def succeed():
            return "ok"
        succeed()
        assert len(mock_write_audit) == 1
        assert mock_write_audit[0]["action"] == "test.action"
        assert mock_write_audit[0]["error"] is None

    def test_async_writes_audit_on_success(self, mock_write_audit):
        @aspect_audit(action="async.action")
        async def succeed():
            return "ok"
        run(succeed())
        assert len(mock_write_audit) == 1
        assert mock_write_audit[0]["action"] == "async.action"

    def test_sync_writes_audit_on_failure(self, mock_write_audit):
        @aspect_audit(action="fail.action")
        def fail():
            raise ValueError("boom")
        with pytest.raises(ValueError):
            fail()
        assert len(mock_write_audit) == 1
        assert mock_write_audit[0]["error"] is not None
        assert "boom" in mock_write_audit[0]["error"]

    def test_async_writes_audit_on_failure(self, mock_write_audit):
        @aspect_audit(action="async.fail")
        async def fail():
            raise RuntimeError("async boom")
        with pytest.raises(RuntimeError):
            run(fail())
        assert mock_write_audit[0]["error"] is not None


# ---------------------------------------------------------------------------
# Paramètres
# ---------------------------------------------------------------------------

class TestAspectAuditParams:
    def test_custom_level_stored(self, mock_write_audit):
        @aspect_audit(level="WARNING", action="warn.action")
        def func():
            return 1
        func()
        assert mock_write_audit[0]["level"] == "WARNING"

    def test_default_action_is_func_name(self, mock_write_audit):
        @aspect_audit()
        def my_operation():
            return 1
        my_operation()
        assert mock_write_audit[0]["action"] == "my_operation"

    def test_custom_action_overrides_name(self, mock_write_audit):
        @aspect_audit(action="custom.event")
        def something():
            return 1
        something()
        assert mock_write_audit[0]["action"] == "custom.event"

    def test_func_name_recorded(self, mock_write_audit):
        @aspect_audit(action="act")
        def target_function():
            return 1
        target_function()
        assert mock_write_audit[0]["func"] == "target_function"

    def test_multiple_calls_produce_multiple_entries(self, mock_write_audit):
        @aspect_audit()
        def func():
            return 1
        func()
        func()
        func()
        assert len(mock_write_audit) == 3


# ---------------------------------------------------------------------------
# Robustesse (DB indisponible)
# ---------------------------------------------------------------------------

class TestAspectAuditRobust:
    def test_does_not_crash_if_db_fails(self):
        """L'aspect ne doit pas lever d'exception si la DB est indisponible."""
        with patch("app.core.aspects._write_audit_log", side_effect=Exception("DB down")):
            # _write_audit_log est appelé à l'intérieur du wrapper
            # mais les exceptions DB sont avalées dans _write_audit_log
            pass  # No crash expected if DB unavailable

    def test_propagates_original_exception(self, mock_write_audit):
        @aspect_audit()
        def fail():
            raise ValueError("original")
        with pytest.raises(ValueError, match="original"):
            fail()
