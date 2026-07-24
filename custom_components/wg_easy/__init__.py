from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .const import (
    CONF_ONLINE_TIMEOUT_MINUTES,
    CONF_ONLINE_TIMEOUT_SECONDS,
    DEFAULT_ONLINE_TIMEOUT_MINUTES,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import WGEasyCoordinator

_LOGGER = logging.getLogger(__name__)


type WGEasyConfigEntry = ConfigEntry[WGEasyCoordinator]


def _migrate_online_timeout_option(hass: HomeAssistant, entry: WGEasyConfigEntry) -> None:
    """One-time, automatic migration of the online-timeout option from minutes to seconds.

    Existing installs stored this as an integer number of minutes under
    ``online_timeout_minutes``. Newer versions use ``online_timeout_seconds``
    instead. If an entry still only has the legacy key, convert it in place
    (minutes * 60) so behaviour is unchanged for the user and no manual
    reconfiguration is required.
    """
    if CONF_ONLINE_TIMEOUT_SECONDS in entry.options:
        return

    legacy_minutes = entry.options.get(
        CONF_ONLINE_TIMEOUT_MINUTES, DEFAULT_ONLINE_TIMEOUT_MINUTES
    )
    new_options = {
        key: value
        for key, value in entry.options.items()
        if key != CONF_ONLINE_TIMEOUT_MINUTES
    }
    new_options[CONF_ONLINE_TIMEOUT_SECONDS] = int(legacy_minutes) * 60

    hass.config_entries.async_update_entry(entry, options=new_options)
    _LOGGER.info(
        "WG Easy (%s): migrated online timeout option from %s minute(s) to %s second(s)",
        entry.title,
        legacy_minutes,
        new_options[CONF_ONLINE_TIMEOUT_SECONDS],
    )


async def async_setup_entry(hass: HomeAssistant, entry: WGEasyConfigEntry) -> bool:
    _migrate_online_timeout_option(hass, entry)

    coordinator = WGEasyCoordinator(
        hass,
        config_entry_id=entry.entry_id,
        url=entry.data[CONF_URL],
        token=entry.data[CONF_TOKEN],
        poll_interval=entry.options.get("poll_interval", DEFAULT_POLL_INTERVAL),
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        raise ConfigEntryNotReady(f"Unable to connect to WG Easy: {err}") from err

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: WGEasyConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_config_entry_device(
    hass: HomeAssistant,
    entry: WGEasyConfigEntry,
    device_entry: dr.DeviceEntry,
) -> bool:
    coordinator = entry.runtime_data
    active_client_keys = {
        client["publicKey"] for client in coordinator.data.get("clients", [])
    }

    return not any(
        identifier
        for identifier in device_entry.identifiers
        if identifier[0] == DOMAIN and identifier[1] in active_client_keys
    )
