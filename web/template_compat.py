"""
web/template_compat.py — Compatibility shim for Starlette TemplateResponse signature changes.
"""
from __future__ import annotations

import inspect
from typing import Any


def template_response(
    templates: Any,
    request: Any,
    name: str,
    context: dict[str, Any],
    *,
    status_code: int = 200,
):
    """
    Render a Jinja template across Starlette versions.

    Starlette >= 1.0:
        TemplateResponse(request, name, context, status_code=...)
    Starlette < 1.0:
        TemplateResponse(name, context, status_code=...)
    """
    fn = templates.TemplateResponse
    params = inspect.signature(fn).parameters
    if "request" in params:
        return fn(request, name, context, status_code=status_code)
    return fn(name, context, status_code=status_code)

