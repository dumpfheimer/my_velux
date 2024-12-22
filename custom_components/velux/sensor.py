"""Support for VELUX sensors."""
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from pyvlx import PyVLX

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up sensor(s) for Velux platform."""
    entities = []
    pyvlx: PyVLX = hass.data[DOMAIN][entry.entry_id]
    entities.append(VeluxConnectionCounter(pyvlx, entry))
    entities.append(VeluxConnectionState(pyvlx, entry))
    async_add_entities(entities)


class VeluxConnectionCounter(SensorEntity):
    """Representation of a Velux number."""

    def __init__(self, pyvlx: PyVLX, entry: ConfigEntry) -> None:
        """Initialize the cover."""
        self.pyvlx: PyVLX = pyvlx
        self.entry: ConfigEntry = entry

    @property
    def name(self) -> str:
        """Name of the entity."""
        return "Connection Counter"

    @property
    def device_info(self) -> DeviceInfo:
        """Return specific device attributes."""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "connections": {("Host", self.pyvlx.config.host)},
            "name": "KLF200 Gateway",
            "manufacturer": "Velux",
            "sw_version": self.pyvlx.version,
        }

    @property
    def unique_id(self) -> str:
        """Return the unique ID of this cover."""
        return f"{self.entry.unique_id}_connection_counter"

    @property
    def native_value(self) -> int:
        """Return the value reported by the sensor."""
        return self.pyvlx.connection.connection_counter


class VeluxConnectionState(BinarySensorEntity):
    """Representation of a Velux state."""

    def __init__(self, pyvlx: PyVLX, entry: ConfigEntry):
        """Initialize the cover."""
        self.pyvlx: PyVLX = pyvlx
        self.entry: ConfigEntry = entry

    @property
    def is_on(self):
        """Return the device state of the entity"""
        return self.pyvlx.connection.connected

    @property
    def device_class(self):
        """Return the device state of the entity"""
        return BinarySensorDeviceClass.CONNECTIVITY

    @property
    def name(self):
        """Name of the entity."""
        return "Connection State"

    @property
    def device_info(self):
        """Device info of the binary sensor."""
        return {
            "identifiers": {
                (DOMAIN, self.unique_id)
            },
            "connections": {
                ("Host", self.pyvlx.config.host)
            },
            "name": "KLF200 Gateway",
            "manufacturer": "Velux",
            "sw_version": self.pyvlx.version,
        }

    @property
    def unique_id(self):
        """Return the unique ID of this cover."""
        return f"{self.entry.unique_id}_connection_state"

    @callback
    async def after_update_callback(self):
        """Call after device was updated."""
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register callbacks to update hass after device was changed."""
        self.pyvlx.connection.register_connection_opened_cb(self.after_update_callback)
        self.pyvlx.connection.register_connection_closed_cb(self.after_update_callback)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister callbacks to update hass after device was changed."""
        self.pyvlx.connection.unregister_connection_opened_cb(self.after_update_callback)
        self.pyvlx.connection.unregister_connection_closed_cb(self.after_update_callback)
