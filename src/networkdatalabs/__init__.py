"""Official client for the Network Data Labs API. Standard library only (urllib)."""
from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

__all__ = ["NetworkDataLabs", "NetworkDataLabsError", "__version__"]
__version__ = "0.1.0"

DEFAULT_BASE_URL = "https://api.networkdatalabs.com"


class NetworkDataLabsError(Exception):
    """Raised for non-2xx responses and network errors/timeouts (``status`` 0,
    ``code`` ``NETWORK_ERROR``). Has ``status``, ``code`` and ``body``."""

    def __init__(self, status: int, body: Any):
        err = body.get("error") if isinstance(body, dict) else None
        self.status = status
        self.code: Optional[str] = err.get("code") if isinstance(err, dict) else None
        self.body = body
        msg = err.get("message") if isinstance(err, dict) else None
        super().__init__(f"{self.code or 'HTTP_' + str(status)}: {msg}" if msg else f"HTTP {status}")


class NetworkDataLabs:
    """Client for https://api.networkdatalabs.com.

    Risk flags (is_tor, is_vpn, is_relay, is_hosting) are returned on paid
    plans only; on Free they are omitted from ``traits``.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: str = DEFAULT_BASE_URL, timeout: float = 10.0):
        self.api_key = api_key or os.environ.get("NDL_API_KEY")
        if not self.api_key:
            raise ValueError("Missing API key: pass api_key= or set NDL_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def lookup(self, ip: Optional[str] = None) -> Dict[str, Any]:
        """Look up an IPv4/IPv6 address; omit ``ip`` for the caller's own IP."""
        path = f"/v0/ip/{urllib.parse.quote(ip, safe='')}" if ip else "/v0/ip"
        return self._request("GET", path)

    def me(self) -> Dict[str, Any]:
        """Caller IP, plan, current-period usage and limits."""
        return self._request("GET", "/v0/me")

    def bulk(self, ips: List[str]) -> Dict[str, Any]:
        """Look up up to 100 IPs in one request (paid plans). Returns {results, errors}."""
        ips = list(ips)
        if not ips:
            raise ValueError("bulk() needs at least one IP")
        if len(ips) > 100:
            raise ValueError("bulk() accepts at most 100 IPs per request")
        return self._request("POST", "/v0/bulk", {"ips": ips})

    def _request(self, method: str, path: str, body: Any = None) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": f"networkdatalabs-python/{__version__}",
        }
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(self.base_url + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as res:
                return json.loads(res.read() or b"null")
        except urllib.error.HTTPError as e:
            raw = e.read()
            try:
                parsed: Any = json.loads(raw)
            except ValueError:
                parsed = raw.decode(errors="replace")
            raise NetworkDataLabsError(e.code, parsed) from None
        except (urllib.error.URLError, socket.timeout, TimeoutError) as e:
            reason = getattr(e, "reason", e)
            raise NetworkDataLabsError(0, {"error": {"code": "NETWORK_ERROR", "message": str(reason)}}) from e
