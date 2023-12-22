"""Velux component config flow."""
# https://developers.home-assistant.io/docs/config_entries_config_flow_handler#defining-your-config-flow
from typing import Any

import voluptuous as vol
from homeassistant.components.zeroconf import ZeroconfServiceInfo
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult
from pyvlx import PyVLX, PyVLXException

from .const import DOMAIN

RESULT_AUTH_FAILED = "connection_failed"
RESULT_SUCCESS = "success"


class VeluxConfigFlow(ConfigFlow, domain=DOMAIN):
    """Velux config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the Velux flow."""
        self._host: str | None = None

    async def async_step_import(self, data: dict[str, Any] | None = None) -> FlowResult:
        """Handle configuration by yaml file."""
        return await self.async_step_user(user_input=data)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle configuration via user input."""
        errors = {}
        if user_input is not None:
            self._async_abort_entries_match({CONF_HOST: user_input[CONF_HOST]})
            pyvlx: PyVLX = PyVLX(
                host=user_input[CONF_HOST],
                password=user_input[CONF_PASSWORD],
            )
            try:
                await pyvlx.connect()
                await pyvlx.disconnect()
                return self.async_create_entry(
                    title=user_input[CONF_HOST],
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )
            except ConnectionAbortedError:
                errors["base"] = "cannot_connect"
            except OSError:
                errors["base"] = "invalid_host"
            except PyVLXException:
                errors["base"] = "invalid_auth"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=self._host): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_unignore(self, user_input: dict[str, Any]) -> FlowResult:
        """Rediscover a previously ignored discover."""
        self._async_abort_entries_match({CONF_HOST: user_input[CONF_HOST]})
        return await self.async_step_user()

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle discovery by zeroconf."""
        if not discovery_info.name.startswith("VELUX_KLF_LAN"):
            return self.async_abort(reason="no_devices_found")
        self._async_abort_entries_match({CONF_HOST: discovery_info.host})
        self._host = discovery_info.host
        return await self.async_step_user()
