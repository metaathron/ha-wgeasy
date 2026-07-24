from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_TOKEN, CONF_URL
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WGEasyApiError, async_detect_api_version
from .const import (
    API_VERSION_AUTO,
    API_VERSIONS,
    CONF_API_VERSION,
    CONF_RESOLVED_API_VERSION,
    DEFAULT_ONLINE_TIMEOUT_SECONDS,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class WGEasyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def _async_validate(self, user_input: dict) -> tuple[dict | None, dict]:
        """Try to connect with the given input, resolving auto/v14/v15.

        Returns a (data_to_store, errors) tuple. data_to_store is None if
        validation failed, in which case errors is populated instead.
        """
        url = user_input[CONF_URL]
        token = user_input.get(CONF_TOKEN) or None
        password = user_input.get(CONF_PASSWORD) or None
        requested_version = user_input.get(CONF_API_VERSION, API_VERSION_AUTO)

        session = async_get_clientsession(self.hass)

        try:
            resolved_version, _client = await async_detect_api_version(
                session,
                url,
                token=token,
                password=password,
                requested_version=requested_version,
            )
        except WGEasyApiError as err:
            _LOGGER.debug("WG Easy connection validation failed: %s", err)
            return None, {"base": "cannot_connect"}

        data = {
            CONF_URL: url,
            CONF_API_VERSION: requested_version,
            CONF_RESOLVED_API_VERSION: resolved_version,
        }
        if token:
            data[CONF_TOKEN] = token
        if password:
            data[CONF_PASSWORD] = password
        return data, {}

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_URL])
            self._abort_if_unique_id_configured()

            data, errors = await self._async_validate(user_input)
            if data is not None:
                return self.async_create_entry(title="WG Easy", data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=self._build_schema(),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input=None):
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_URL])
            self._abort_if_unique_id_mismatch(reason="wrong_account")

            data, errors = await self._async_validate(user_input)
            if data is not None:
                return self.async_update_reload_and_abort(
                    entry,
                    unique_id=user_input[CONF_URL],
                    data_updates=data,
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self._build_schema(entry.data),
            errors=errors,
        )

    def _build_schema(self, data=None):
        data = data or {}
        return vol.Schema(
            {
                vol.Required(CONF_URL, default=data.get(CONF_URL, "")): str,
                vol.Required(
                    CONF_API_VERSION,
                    default=data.get(CONF_API_VERSION, API_VERSION_AUTO),
                ): vol.In(API_VERSIONS),
                vol.Optional(CONF_TOKEN, default=data.get(CONF_TOKEN, "")): str,
                vol.Optional(CONF_PASSWORD, default=data.get(CONF_PASSWORD, "")): str,
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return WGEasyOptionsFlow(config_entry)


class WGEasyOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(
                    "poll_interval",
                    default=self._config_entry.options.get(
                        "poll_interval", DEFAULT_POLL_INTERVAL
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=5)),
                vol.Required(
                    "online_timeout_seconds",
                    default=self._config_entry.options.get(
                        "online_timeout_seconds", DEFAULT_ONLINE_TIMEOUT_SECONDS
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=1)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)
