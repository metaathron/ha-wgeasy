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
    """Talks to a wg-easy v15+ style API: a single endpoint secured with a bearer token."""

    def __init__(self, session: ClientSession, url: str, token: str | None) -> None:
        self._session = session
        self._url = url
        self._token = token

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


async def async_detect_api_version(
    session: ClientSession,
    url: str,
    *,
    token: str | None,
    password: str | None,
    requested_version: str,
) -> tuple[str, "WGEasyV14Client | WGEasyV15Client"]:
    """Resolve which wg-easy API version to use and return a ready client for it.

    - requested_version == "v14" or "v15": only that method is tried (manual override).
    - requested_version == "auto": tries whichever credentials were supplied,
      password/v14 first, then token/v15, and keeps the first one that works.
    """
    # Imported locally to avoid a circular import between api.py and const.py callers.
    from .const import API_VERSION_V14, API_VERSION_V15

    candidates: list[tuple[str, Any]] = []
    if requested_version == API_VERSION_V14:
        candidates = [(API_VERSION_V14, password)]
    elif requested_version == API_VERSION_V15:
        candidates = [(API_VERSION_V15, token)]
    else:
        if password:
            candidates.append((API_VERSION_V14, password))
        if token:
            candidates.append((API_VERSION_V15, token))

    if not candidates:
        raise WGEasyApiError(
            "Provide an API token (v15), a password (v14), or both for auto-detection."
        )

    last_error: WGEasyApiError | None = None
    for version, credential in candidates:
        client: WGEasyV14Client | WGEasyV15Client
        if version == API_VERSION_V14:
            client = WGEasyV14Client(session, url, credential)
        else:
            client = WGEasyV15Client(session, url, credential)

        try:
            await client.async_fetch_raw()
        except WGEasyApiError as err:
            _LOGGER.debug("WG Easy %s probe failed: %s", version, err)
            last_error = err
            continue
        else:
            return version, client

    assert last_error is not None
    raise last_error
