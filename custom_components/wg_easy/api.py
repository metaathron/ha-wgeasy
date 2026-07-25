from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientError, ClientSession

_LOGGER = logging.getLogger(__name__)


class WGEasyApiError(Exception):
    """Raised when the WG Easy API cannot be reached or returns an error."""


class WGEasyAuthError(WGEasyApiError):
    """Raised when authentication with the WG Easy API fails."""


class WGEasyV15Client:
    """Talks to wg-easy v15's Bearer-token-secured metrics endpoint.

    v15 has no general Bearer-token JSON API - the only endpoint secured by
    a Bearer token is the metrics feature (Admin Panel -> General ->
    Metrics), and its JSON variant at "{base_url}/metrics/json" returns
    exactly the {clients: [...], wireguard_configured_peers, ...} shape
    this integration expects (confirmed against wg-easy's own
    src/server/routes/metrics/json.get.ts). The general "/api/..." REST
    API is Basic Auth only and unrelated to this token.

    The configured URL is treated as the server's base address (optionally
    including a reverse-proxy subpath, e.g. "https://host/wireguard") and
    "/metrics/json" is appended automatically unless it's already there,
    so entering just the base address is enough.
    """

    def __init__(self, session: ClientSession, url: str, token: str | None) -> None:
        self._session = session
        self._url = self._normalize_url(url)
        self._token = token

    @staticmethod
    def _normalize_url(url: str) -> str:
        base = (url or "").rstrip("/")
        if base.endswith("/metrics/json"):
            return base
        return f"{base}/metrics/json"

    async def async_fetch_raw(self) -> bytes:
        if not self._token:
            raise WGEasyApiError("No API token configured for the v15 API")

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }
        try:
            async with self._session.get(self._url, headers=headers) as response:
                if response.status == 401:
                    raise WGEasyAuthError("Unauthorized - check API token")
                if response.status >= 400:
                    body = await response.text()
                    raise WGEasyApiError(f"HTTP {response.status}: {body[:200]}")
                return await response.read()
        except ClientError as err:
            raise WGEasyApiError(f"Request failed: {err}") from err


class WGEasyV14Client:
    """Talks to a wg-easy v14 style API: password login -> session cookie -> REST endpoint."""

    def __init__(self, session: ClientSession, url: str, password: str | None) -> None:
        self._session = session
        self._base_url = url.rstrip("/")
        self._password = password
        self._session_cookie: str | None = None

    async def _async_login(self) -> None:
        if not self._password:
            raise WGEasyApiError("No password configured for the v14 API")

        session_url = f"{self._base_url}/api/session"
        try:
            async with self._session.post(
                session_url, json={"password": self._password}
            ) as response:
                if response.status == 401:
                    raise WGEasyAuthError("Unauthorized - check password")
                if response.status >= 400:
                    body = await response.text()
                    raise WGEasyApiError(f"Login HTTP {response.status}: {body[:200]}")

                try:
                    login_data = await response.json()
                except ValueError as err:
                    raise WGEasyApiError(f"Invalid login response: {err}") from err

                if isinstance(login_data, dict) and login_data.get("success") is False:
                    raise WGEasyAuthError("wg-easy rejected the configured password")

                cookie = response.cookies.get("connect.sid")
                if not cookie:
                    raise WGEasyApiError("Login succeeded but no session cookie was returned")
                self._session_cookie = cookie.value
        except ClientError as err:
            raise WGEasyApiError(f"Login request failed: {err}") from err

    async def async_fetch_raw(self) -> bytes:
        if not self._session_cookie:
            await self._async_login()

        data_url = f"{self._base_url}/api/wireguard/client"
        cookies = {"connect.sid": self._session_cookie} if self._session_cookie else {}

        try:
            async with self._session.get(
                data_url, headers={"Accept": "application/json"}, cookies=cookies
            ) as response:
                if response.status == 401:
                    # Session likely expired; drop it so the next poll logs in again.
                    self._session_cookie = None
                    raise WGEasyAuthError("Session expired - will re-authenticate next poll")
                if response.status >= 400:
                    body = await response.text()
                    raise WGEasyApiError(f"HTTP {response.status}: {body[:200]}")
                return await response.read()
        except ClientError as err:
            raise WGEasyApiError(f"Request failed: {err}") from err


async def async_probe_wg_easy_version(session: ClientSession, url: str) -> str:
    """Unauthenticated probe to tell wg-easy v14 apart from v15, before any credentials.

    wg-easy v14 exposes an unauthenticated ``GET {base_url}/api/release`` that
    returns the running release as a bare JSON string (confirmed against
    v14's src/lib/Server.js: it's registered on the router before the
    password-check middleware). wg-easy v15's rewrite has no endpoint at
    that path at all. So: a 200 with a non-empty string body means v14;
    any other response from a server that *did* respond (404, etc.) means
    it's not v14 - treat it as v15. A connection failure (bad URL, DNS,
    refused, timeout) is raised so the caller can show a URL/reachability
    error before ever asking for credentials.
    """
    # Imported locally to avoid a circular import with const.py's importers.
    from .const import API_VERSION_V14, API_VERSION_V15

    base_url = (url or "").rstrip("/")
    probe_url = f"{base_url}/api/release"

    try:
        async with session.get(probe_url) as response:
            if response.status == 200:
                try:
                    body = await response.json(content_type=None)
                except ValueError:
                    body = None
                if isinstance(body, str) and body.strip():
                    return API_VERSION_V14
            return API_VERSION_V15
    except ClientError as err:
        raise WGEasyApiError(f"Could not reach {base_url}: {err}") from err
