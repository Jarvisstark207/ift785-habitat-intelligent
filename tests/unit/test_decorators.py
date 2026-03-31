"""
Tests unitaires - Décorateurs transversaux (Itération 8)
Couvre : @log_call, @validate_input, @require_role
"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from pydantic import BaseModel

from app.core.decorators import log_call, validate_input, require_role


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(coro):
    """Execute une coroutine de façon synchrone dans les tests."""
    return asyncio.get_event_loop().run_until_complete(coro)


def make_mock_request(token: str):
    """Crée un mock de requête FastAPI avec un header Authorization."""
    mock = MagicMock()
    mock.headers = {"Authorization": f"Bearer {token}"}
    return mock


class SampleSchema(BaseModel):
    name: str
    value: int


# ---------------------------------------------------------------------------
# @log_call
# ---------------------------------------------------------------------------

class TestLogCall:
    def test_preserves_function_name(self):
        @log_call
        def my_function():
            pass
        assert my_function.__name__ == "my_function"

    def test_preserves_async_function_name(self):
        @log_call
        async def my_async_function():
            pass
        assert my_async_function.__name__ == "my_async_function"

    def test_preserves_docstring(self):
        @log_call
        def documented():
            """Ma docstring."""
        assert documented.__doc__ == "Ma docstring."

    def test_sync_returns_value(self):
        @log_call
        def add(a, b):
            return a + b
        assert add(2, 3) == 5

    def test_async_returns_value(self):
        @log_call
        async def fetch():
            return 42
        assert run(fetch()) == 42

    def test_sync_propagates_exception(self):
        @log_call
        def boom():
            raise ValueError("oops")
        with pytest.raises(ValueError, match="oops"):
            boom()

    def test_async_propagates_exception(self):
        @log_call
        async def async_boom():
            raise RuntimeError("async oops")
        with pytest.raises(RuntimeError, match="async oops"):
            run(async_boom())

    def test_sync_logs_call(self, caplog):
        import logging
        with caplog.at_level(logging.INFO, logger="app.core.decorators"):
            @log_call
            def hello():
                return "hi"
            hello()
        assert "hello" in caplog.text

    def test_async_logs_call(self, caplog):
        import logging
        with caplog.at_level(logging.INFO, logger="app.core.decorators"):
            @log_call
            async def greet():
                return "hello"
            run(greet())
        assert "greet" in caplog.text

    def test_wraps_applied_sync(self):
        @log_call
        def target():
            """target doc"""
        assert target.__name__ == "target"
        assert target.__doc__ == "target doc"

    def test_wraps_applied_async(self):
        @log_call
        async def async_target():
            """async target doc"""
        assert async_target.__name__ == "async_target"
        assert async_target.__doc__ == "async target doc"

    def test_passes_args_correctly(self):
        @log_call
        def multiply(x, y):
            return x * y
        assert multiply(3, 4) == 12

    def test_passes_kwargs_correctly(self):
        @log_call
        def greet(name="World"):
            return f"Hello, {name}!"
        assert greet(name="Alice") == "Hello, Alice!"


# ---------------------------------------------------------------------------
# @validate_input
# ---------------------------------------------------------------------------

class TestValidateInput:
    def test_preserves_function_name(self):
        @validate_input(SampleSchema)
        def handler(data):
            return data
        assert handler.__name__ == "handler"

    def test_valid_dict_passes(self):
        @validate_input(SampleSchema)
        def handler(data):
            return "ok"
        result = handler({"name": "test", "value": 1})
        assert result == "ok"

    def test_invalid_dict_raises_422(self):
        @validate_input(SampleSchema)
        def handler(data):
            return "ok"
        with pytest.raises(HTTPException) as exc_info:
            handler({"name": "test"})  # missing 'value'
        assert exc_info.value.status_code == 422

    def test_valid_pydantic_model_passes(self):
        @validate_input(SampleSchema)
        def handler(data):
            return "ok"
        model = SampleSchema(name="test", value=5)
        result = handler(model)
        assert result == "ok"

    def test_async_valid_dict_passes(self):
        @validate_input(SampleSchema)
        async def handler(data):
            return "ok"
        result = run(handler({"name": "test", "value": 2}))
        assert result == "ok"

    def test_async_invalid_dict_raises_422(self):
        @validate_input(SampleSchema)
        async def handler(data):
            return "ok"
        with pytest.raises(HTTPException) as exc_info:
            run(handler({"value": 2}))  # missing 'name'
        assert exc_info.value.status_code == 422

    def test_preserves_async_function_name(self):
        @validate_input(SampleSchema)
        async def async_handler(data):
            pass
        assert async_handler.__name__ == "async_handler"

    def test_wrong_type_raises_422(self):
        @validate_input(SampleSchema)
        def handler(data):
            return "ok"
        with pytest.raises(HTTPException) as exc_info:
            handler({"name": "test", "value": "not_an_int"})
        assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# @require_role
# ---------------------------------------------------------------------------

class TestRequireRole:
    def test_injects_request_into_signature(self):
        import inspect

        @require_role("user")
        async def endpoint():
            return "ok"

        sig = inspect.signature(endpoint)
        assert "request" in sig.parameters

    def test_preserves_function_name(self):
        @require_role("admin")
        async def admin_endpoint():
            pass
        assert admin_endpoint.__name__ == "admin_endpoint"

    def test_admin_token_allows_admin_endpoint(self):
        @require_role("admin")
        async def endpoint(**kwargs):
            return "allowed"

        mock_req = make_mock_request("token_admin")
        result = run(endpoint(request=mock_req))
        assert result == "allowed"

    def test_user_token_allows_user_endpoint(self):
        @require_role("user")
        async def endpoint(**kwargs):
            return "allowed"

        mock_req = make_mock_request("token_user")
        result = run(endpoint(request=mock_req))
        assert result == "allowed"

    def test_admin_token_allows_user_endpoint(self):
        @require_role("user")
        async def endpoint(**kwargs):
            return "allowed"

        mock_req = make_mock_request("token_admin")
        result = run(endpoint(request=mock_req))
        assert result == "allowed"

    def test_guest_token_blocked_from_admin_endpoint(self):
        @require_role("admin")
        async def endpoint(**kwargs):
            return "allowed"

        mock_req = make_mock_request("token_guest")
        with pytest.raises(HTTPException) as exc_info:
            run(endpoint(request=mock_req))
        assert exc_info.value.status_code == 403

    def test_guest_token_blocked_from_user_endpoint(self):
        @require_role("user")
        async def endpoint(**kwargs):
            return "allowed"

        mock_req = make_mock_request("token_guest")
        with pytest.raises(HTTPException) as exc_info:
            run(endpoint(request=mock_req))
        assert exc_info.value.status_code == 403

    def test_missing_token_raises_401(self):
        @require_role("admin")
        async def endpoint(**kwargs):
            return "allowed"

        mock_req = make_mock_request("token_invalid_xyz")
        with pytest.raises(HTTPException) as exc_info:
            run(endpoint(request=mock_req))
        assert exc_info.value.status_code == 401

    def test_no_request_raises_401(self):
        @require_role("admin")
        async def endpoint(**kwargs):
            return "allowed"

        with pytest.raises(HTTPException) as exc_info:
            run(endpoint())
        assert exc_info.value.status_code == 401

    def test_composable_with_log_call(self):
        @log_call
        @require_role("admin")
        async def endpoint(**kwargs):
            return "ok"

        mock_req = make_mock_request("token_admin")
        result = run(endpoint(request=mock_req))
        assert result == "ok"

    def test_composable_order_independent(self):
        @require_role("admin")
        @log_call
        async def endpoint(**kwargs):
            return "ok"

        mock_req = make_mock_request("token_admin")
        result = run(endpoint(request=mock_req))
        assert result == "ok"
