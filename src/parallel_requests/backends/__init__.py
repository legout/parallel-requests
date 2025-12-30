from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

from .base import Backend, NormalizedResponse, RequestConfig

if TYPE_CHECKING:
    from .aiohttp import AiohttpBackend
    from .httpx import HttpxBackend
    from .niquests import NiquestsBackend
    from .requests import RequestsBackend


_LAZY_BACKENDS: dict[str, tuple[str, str, str]] = {
    "NiquestsBackend": ("niquests", "NiquestsBackend", "niquests"),
    "HttpxBackend": ("httpx", "HttpxBackend", "httpx"),
    "AiohttpBackend": ("aiohttp", "AiohttpBackend", "aiohttp"),
    "RequestsBackend": ("requests", "RequestsBackend", "requests"),
}

__all__ = [
    "Backend",
    "RequestConfig",
    "NormalizedResponse",
    "NiquestsBackend",
    "HttpxBackend",
    "AiohttpBackend",
    "RequestsBackend",
]


def __getattr__(name: str) -> object:
    lazy_backend = _LAZY_BACKENDS.get(name)
    if lazy_backend is None:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    backend_module, backend_class, dependency_module = lazy_backend
    try:
        module = importlib.import_module(f"{__name__}.{backend_module}")
    except ModuleNotFoundError as e:
        if e.name is not None and (
            e.name == dependency_module or e.name.startswith(f"{dependency_module}.")
        ):
            raise ImportError(
                f"{backend_class} requires the optional dependency '{dependency_module}'. "
                f"Install it with 'parallel-requests[{dependency_module}]' or 'pip install {dependency_module}'."
            ) from e
        raise

    return getattr(module, backend_class)


def __dir__() -> list[str]:
    return sorted(set(globals().keys()) | set(__all__))
