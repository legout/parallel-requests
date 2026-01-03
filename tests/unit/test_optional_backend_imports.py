import builtins
import importlib
import sys
import types
from typing import Any

import pytest

from fastreq.backends.base import Backend, NormalizedResponse, RequestConfig
from fastreq.client import ParallelRequests


def _clear_fastreq_modules() -> None:
    for module_name in list(sys.modules.keys()):
        if module_name == "fastreq" or module_name.startswith("fastreq."):
            sys.modules.pop(module_name, None)


def _block_imports(monkeypatch: pytest.MonkeyPatch, blocked_modules: set[str]) -> None:
    real_import = builtins.__import__

    def guarded_import(
        name: str,
        globals: dict[str, Any] | None = None,
        locals: dict[str, Any] | None = None,
        fromlist: tuple[str, ...] | list[str] = (),
        level: int = 0,
    ) -> Any:
        if name in blocked_modules or any(name.startswith(f"{m}.") for m in blocked_modules):
            raise ModuleNotFoundError(f"No module named '{name}'", name=name)
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)


def test_import_fastreq_without_optional_backends(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_fastreq_modules()

    _block_imports(monkeypatch, {"aiohttp", "niquests", "requests"})

    module = importlib.import_module("fastreq")
    assert hasattr(module, "ParallelRequests")

    _clear_fastreq_modules()
    importlib.import_module("fastreq")


def test_import_fastreq_backends_without_optional_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_fastreq_modules()

    _block_imports(monkeypatch, {"aiohttp", "niquests", "requests"})

    backends = importlib.import_module("fastreq.backends")
    assert hasattr(backends, "Backend")
    assert hasattr(backends, "RequestConfig")
    assert hasattr(backends, "NormalizedResponse")

    _clear_fastreq_modules()
    importlib.import_module("fastreq")


def test_accessing_missing_backend_raises_importerror(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_fastreq_modules()

    _block_imports(monkeypatch, {"aiohttp"})

    backends = importlib.import_module("fastreq.backends")

    with pytest.raises(ImportError) as excinfo:
        getattr(backends, "AiohttpBackend")

    assert "aiohttp" in str(excinfo.value)

    _clear_fastreq_modules()
    importlib.import_module("fastreq")


class _DummyNiquestsBackend(Backend):
    @property
    def name(self) -> str:
        return "niquests"

    async def request(self, config: RequestConfig) -> NormalizedResponse:
        raise NotImplementedError

    async def close(self) -> None:
        return None

    async def __aenter__(self) -> "_DummyNiquestsBackend":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    def supports_http2(self) -> bool:
        return True


def test_auto_backend_selection_does_not_import_unselected_modules(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_find_spec = importlib.util.find_spec
    real_import_module = importlib.import_module

    def fake_find_spec(name: str, package: str | None = None) -> object | None:
        if name == "niquests":
            return object()
        if name in {"aiohttp", "requests"}:
            return None
        return real_find_spec(name, package)

    fake_niquests_module = types.SimpleNamespace(NiquestsBackend=_DummyNiquestsBackend)

    def fake_import_module(name: str, package: str | None = None) -> Any:
        if name == "fastreq.backends.niquests":
            return fake_niquests_module
        if name in {"fastreq.backends.aiohttp", "fastreq.backends.requests"}:
            raise AssertionError(f"Unexpected import of {name}")
        return real_import_module(name, package)

    monkeypatch.setattr(importlib.util, "find_spec", fake_find_spec)
    monkeypatch.setattr(importlib, "import_module", fake_import_module)

    client = ParallelRequests(backend="auto")
    assert client._backend is not None
    assert client._backend.name == "niquests"
