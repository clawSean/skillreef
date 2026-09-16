"""Tiny requests-like HTTP shim for skill helpers; stdlib only."""

from __future__ import annotations

import json as jsonlib
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class Response:
    def __init__(self, status_code: int, body: bytes):
        self.status_code = status_code
        self.text = body.decode("utf-8", errors="replace")
        self.ok = 200 <= status_code < 300

    def json(self) -> Any:
        return jsonlib.loads(self.text)

    def raise_for_status(self) -> None:
        if not self.ok:
            raise RuntimeError(f"HTTP {self.status_code}: {self.text[:500]}")


def request(
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    json: Any = None,
    headers: dict[str, str] | None = None,
    timeout: int = 120,
) -> Response:
    if params:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{urlencode(params)}"
    body = None
    request_headers = dict(headers or {})
    if json is not None:
        body = jsonlib.dumps(json).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")
    req = Request(url, data=body, headers=request_headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as response:
            return Response(response.status, response.read())
    except HTTPError as error:
        return Response(error.code, error.read())


def post(url: str, **kwargs: Any) -> Response:
    return request("POST", url, **kwargs)


def delete(url: str, **kwargs: Any) -> Response:
    return request("DELETE", url, **kwargs)
