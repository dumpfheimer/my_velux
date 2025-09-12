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
        self.pyvlx = node.pyvlx
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
        # Keep references to callbacks for unregistering
        self._device_updated_cb = None
        self._conn_opened_cb = None
        self._conn_closed_cb = None

    @property
    def node(self) -> Node:
        return self.pyvlx.nodes.__getitem__(self.node_id)

    @node.setter
    def node(self, node: Node):
        self.node_id = node.node_id

    def async_register_callbacks(self) -> None:
        """Register callbacks to update hass after device or connection changes."""

        @callback
        def _device_updated(_device) -> None:
            self.async_write_ha_state()

        @callback
        def _conn_changed() -> None:
            self.async_write_ha_state()

        # store refs to unregister later
        self._device_updated_cb = _device_updated
        self._conn_opened_cb = _conn_changed
        self._conn_closed_cb = _conn_changed

        self.node.register_device_updated_cb(self._device_updated_cb)
        self.pyvlx.connection.register_connection_opened_cb(self._conn_opened_cb)
        self.pyvlx.connection.register_connection_closed_cb(self._conn_closed_cb)

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added to hass."""
        self.async_register_callbacks()

    async def async_will_remove_from_hass(self) -> None:
        """Unregister callbacks when entity is removed from hass."""
        if self._device_updated_cb is not None:
            self.node.unregister_device_updated_cb(self._device_updated_cb)
            self._device_updated_cb = None
        if self._conn_opened_cb is not None:
            self.pyvlx.connection.unregister_connection_opened_cb(self._conn_opened_cb)
            self._conn_opened_cb = None
        if self._conn_closed_cb is not None:
            self.pyvlx.connection.unregister_connection_closed_cb(self._conn_closed_cb)
            self._conn_closed_cb = None
