"""Generic Velux Entity."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from pyvlx import Node

from .const import DOMAIN


class VeluxNodeEntity(Entity):
    """Abstraction for all pyvlx node entities."""

    _attr_should_poll = False

    def __init__(self, node: Node, entry: ConfigEntry) -> None:
        """Initialize the Velux device."""
        self.node_id = node.node_id
        self._attr_unique_id = (
            node.serial_number
            if node.serial_number
            else str(self.node.node_id)
        )
        self._attr_name = node.name if node.name else f"#{node.node_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(self.node.node_id))},
            name=self._attr_name,
            via_device=(DOMAIN, str(entry.unique_id)),
        )

    @property
    def node(self) -> Node:
        return self.pyvlx.nodes.__getitem__(self.node_id)

    @node.setter
    def node(self, node: Node):
        self.node_id = node.node_id

    @callback
    async def after_update_callback(self, device):
        """Call after device was updated."""
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register callbacks to update hass after device was changed."""
        self.node.register_device_updated_cb(self.after_update_callback)

        async def after_update_callback(device):
            """Call after device was updated."""
            self.async_write_ha_state()

        self.node.register_device_updated_cb(after_update_callback)
        self.pyvlx.connection.register_connection_opened_cb(self.after_update_callback)
        self.pyvlx.connection.register_connection_closed_cb(self.after_update_callback)

    async def async_added_to_hass(self):
        """Store register state change callback."""
        self.async_register_callbacks()

    async def async_will_remove_from_hass(self) -> None:
        """Unregister callbacks to update hass after device was changed."""
        self.node.unregister_device_updated_cb(self.after_update_callback)
