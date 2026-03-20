from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from aiohttp import ClientError

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DEFAULT_POLL_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class WGEasyCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(
        self,
        hass,
        *,
        config_entry_id: str,
        url: str,
        token: str,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=max(5, int(poll_interval))),
        )
        self.url = url
        self.token = token
        self.config_entry_id = config_entry_id
        self.session = async_get_clientsession(hass)
        self._known_client_keys: set[str] = set()
        self.peer_map: dict[str, dict[str, Any]] = {}
        self._previous_counters: dict[str, tuple[datetime, int, int]] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }

        try:
            async with self.session.get(self.url, headers=headers) as response:
                if response.status == 401:
                    raise UpdateFailed("Unauthorized – check token")
                if response.status >= 400:
                    body = await response.text()
                    raise UpdateFailed(f"HTTP {response.status}: {body[:200]}")

                payload = await response.json()
        except ClientError as err:
            raise UpdateFailed(f"Request failed: {err}") from err
        except ValueError as err:
            raise UpdateFailed(f"Invalid JSON response: {err}") from err

        data = self._normalize_payload(payload)
        self.peer_map = {client["publicKey"]: client for client in data["clients"]}
        self._remove_stale_devices(set(self.peer_map))
        return data

    def _normalize_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        clients = payload.get("clients") or []
        now = dt_util.utcnow()

        normalized_clients: list[dict[str, Any]] = []
        next_previous_counters: dict[str, tuple[datetime, int, int]] = {}

        for client in clients:
            public_key = client.get("publicKey")
            if not public_key:
                continue

            transfer_rx = int(client.get("transferRx") or 0)
            transfer_tx = int(client.get("transferTx") or 0)
            transfer_rx_rate = 0.0
            transfer_tx_rate = 0.0

            previous = self._previous_counters.get(public_key)
            if previous is not None:
                previous_time, previous_rx, previous_tx = previous
                elapsed = (now - previous_time).total_seconds()
                if elapsed > 0:
                    rx_delta = transfer_rx - previous_rx
                    tx_delta = transfer_tx - previous_tx
                    transfer_rx_rate = max(0.0, rx_delta / elapsed)
                    transfer_tx_rate = max(0.0, tx_delta / elapsed)

            next_previous_counters[public_key] = (now, transfer_rx, transfer_tx)

            normalized_clients.append(
                {
                    **client,
                    "name": client.get("name") or public_key[:8],
                    "transferRx": transfer_rx,
                    "transferTx": transfer_tx,
                    "transferRxRate": round(transfer_rx_rate, 2),
                    "transferTxRate": round(transfer_tx_rate, 2),
                    "endpoint": client.get("endpoint") or None,
                    "ipv4Address": client.get("ipv4Address") or None,
                    "ipv6Address": client.get("ipv6Address") or None,
                    "enabled": bool(client.get("enabled", False)),
                    "latestHandshakeAt": client.get("latestHandshakeAt") or None,
                }
            )

        self._previous_counters = next_previous_counters

        return {
            **payload,
            "clients": normalized_clients,
            "wireguard_configured_peers": payload.get(
                "wireguard_configured_peers", len(normalized_clients)
            ),
            "wireguard_enabled_peers": payload.get(
                "wireguard_enabled_peers",
                sum(1 for client in normalized_clients if client["enabled"]),
            ),
            "wireguard_connected_peers": payload.get(
                "wireguard_connected_peers",
                sum(
                    1
                    for client in normalized_clients
                    if client["latestHandshakeAt"] is not None
                ),
            ),
        }

    def _remove_stale_devices(self, current_client_keys: set[str]) -> None:
        stale_client_keys = self._known_client_keys - current_client_keys
        if not stale_client_keys:
            self._known_client_keys = current_client_keys
            return

        device_registry = dr.async_get(self.hass)

        for client_key in stale_client_keys:
            device = device_registry.async_get_device(identifiers={(DOMAIN, client_key)})
            if device is not None:
                device_registry.async_update_device(
                    device_id=device.id,
                    remove_config_entry_id=self.config_entry_id,
                )
            self._previous_counters.pop(client_key, None)

        self._known_client_keys = current_client_keys
