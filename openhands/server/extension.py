"""OpenHands (OH) server extension system.

This lightweight mechanism lets external repositories (e.g., an enterprise or custom extension)
mount routes, middleware, and lifecycle hooks onto the OH FastAPI app without modifying
OH code or relying on environment-variable-driven class switching everywhere.

Two discovery mechanisms are supported:
- Environment variable OPENHANDS_EXTENSIONS: a comma-separated list of references like
  "pkg.mod:register" or "pkg.mod:MyExtension.register". Each reference must resolve to a
  callable or to an object that exposes a callable attribute `register` (and optional
  `on_startup`, `on_shutdown`).
- Python entry points under group "openhands_server_extensions": each entry point is
  resolved similarly and invoked to register with the app.

Terminology:
- OH refers to the core OpenHands project.
- Enterprise extension or custom extension refers to an external repo that extends OH.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from importlib import import_module
from importlib.metadata import EntryPoint, entry_points
from typing import Callable, Iterable

from fastapi import FastAPI

# Lightweight plugin interface to let external repos extend OpenHands server
# without modifying the core repo or relying on environment-variable-driven
# class switching everywhere.
#
# An extension can expose either of the following callables:
# - register(app: FastAPI) -> None  # mandatory
# - on_startup(app: FastAPI) -> None  # optional
# - on_shutdown(app: FastAPI) -> None  # optional
#
# How to load extensions:
# 1) Environment variable OPENHANDS_EXTENSIONS as comma-separated objects
#    in the form "pkg.mod:register" or "pkg.mod:MyExtension.register".
# 2) Python entry points: group="openhands_server_extensions"; the object
#    referenced by the entry point will be imported and, if it is a callable,
#    it will be invoked as register(app).
#
# This module intentionally has zero imports from other openhands modules so
# it can be safely imported early and from external packages.


@dataclass(frozen=True)
class ServerExtension:
    name: str
    register: Callable[[FastAPI], None]
    on_startup: Callable[[FastAPI], None] | None = None
    on_shutdown: Callable[[FastAPI], None] | None = None


def _import_object(qualname: str):
    """Import an object from a fully qualified name like 'pkg.mod:attr'."""
    if ':' not in qualname:
        raise ValueError(
            f"Invalid extension reference '{qualname}'. Expected format 'pkg.mod:attr'"
        )
    module_name, attr_name = qualname.split(':', 1)
    module = import_module(module_name)
    obj = module
    for part in attr_name.split('.'):
        obj = getattr(obj, part)
    return obj


def _from_env() -> list[ServerExtension]:
    val = os.getenv('OPENHANDS_EXTENSIONS', '').strip()
    if not val:
        return []
    exts: list[ServerExtension] = []
    for raw in [s.strip() for s in val.split(',') if s.strip()]:
        obj = _import_object(raw)
        if not callable(obj):
            # Allow classes with a 'register' attribute
            register = getattr(obj, 'register', None)
            if register is None or not callable(register):
                raise TypeError(
                    f"Extension object '{raw}' is not callable and has no callable 'register'"
                )
            on_startup = getattr(obj, 'on_startup', None)
            on_shutdown = getattr(obj, 'on_shutdown', None)
            exts.append(
                ServerExtension(
                    name=raw,
                    register=register,
                    on_startup=on_startup,
                    on_shutdown=on_shutdown,
                )
            )
        else:
            exts.append(ServerExtension(name=raw, register=obj))
    return exts


def _from_entry_points() -> list[ServerExtension]:
    eps: Iterable[EntryPoint] = entry_points().select(
        group='openhands_server_extensions'
    )
    result: list[ServerExtension] = []
    for ep in eps:
        obj = ep.load()
        if not callable(obj):
            register = getattr(obj, 'register', None)
            if register is None or not callable(register):
                continue
            on_startup = getattr(obj, 'on_startup', None)
            on_shutdown = getattr(obj, 'on_shutdown', None)
            result.append(
                ServerExtension(
                    name=ep.name,
                    register=register,
                    on_startup=on_startup,
                    on_shutdown=on_shutdown,
                )
            )
        else:
            result.append(ServerExtension(name=ep.name, register=obj))
    return result


def discover_extensions() -> list[ServerExtension]:
    """Discover extensions from env var and entry points."""
    # Env has priority; then entry points
    env_exts = _from_env()
    eps_exts = _from_entry_points()
    # Deduplicate by name
    seen = set()
    ordered: list[ServerExtension] = []
    for ext in [*env_exts, *eps_exts]:
        if ext.name in seen:
            continue
        seen.add(ext.name)
        ordered.append(ext)
    return ordered


def mount_extensions(app: FastAPI) -> None:
    """Discover and mount extensions onto the provided FastAPI app."""
    for ext in discover_extensions():
        ext.register(app)
        if ext.on_startup:
            app.add_event_handler('startup', lambda e=ext: e.on_startup(app))
        if ext.on_shutdown:
            app.add_event_handler('shutdown', lambda e=ext: e.on_shutdown(app))
