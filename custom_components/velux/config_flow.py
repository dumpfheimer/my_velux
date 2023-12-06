"""Velux component config flow."""
# https://developers.home-assistant.io/docs/config_entries_config_flow_handler#defining-your-config-flow
import logging
from typing import Any

from pyvlx import PyVLX, PyVLXException
import voluptuous as vol

from homeassistant.components.zeroconf import ZeroconfServiceInfo
from homeassistant.config_entries import ConfigFlow, FlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

RESULT_AUTH_FAILED = "connection_failed"
RESULT_SUCCESS = "success"


class VeluxConfigFlow(ConfigFlow, domain=DOMAIN):
    """Velux config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the Velux flow."""
        self._host: str = None

    async def async_step_import(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle configuration by yaml file."""
        return await self.async_step_user(user_input)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle configuration via user input."""
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()
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
            except PyVLXException:
                errors["base"] = "invalid_auth"
            except OSError:
                errors["base"] = "invalid_host"
            errors["base"] = "cannot_connect"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=self._host): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_unignore(
        self, user_input: dict[str, Any] | None
    ) -> FlowResult:
        """Rediscover a previously ignored discover."""
        unique_id = user_input["unique_id"]
        await self.async_set_unique_id(unique_id)
        return await self.async_step_user()

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle discovery by zeroconf."""
        if (
            discovery_info is None
            or not discovery_info.hostname
            or not discovery_info.hostname.startswith("VELUX_KLF_LAN")
        ):
            return self.async_abort(reason="no_devices_found")
        await self.async_set_unique_id(discovery_info.host)
        self._host = discovery_info.host
        return await self.async_step_user()
