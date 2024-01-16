"""Support for VELUX sensors."""
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
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
    entities.append(VeluxConnectionCounter(pyvlx))
    entities.append(VeluxConnectionState(gateway))
    async_add_entities(entities)


class VeluxConnectionCounter(SensorEntity):
    """Representation of a Velux number."""

    def __init__(self, pyvlx: PyVLX) -> None:
        """Initialize the cover."""
        self.pyvlx: PyVLX = pyvlx

    @property
    def name(self) -> str:
        """Name of the entity."""
        return "KLF200 Connection Counter"

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
        return "KLF200ConnectionCounter"

    @property
    def native_value(self) -> int:
        """Return the value reported by the sensor."""
        return self.pyvlx.connection.connection_counter


class VeluxConnectionState(BinarySensorEntity):
    """Representation of a Velux state."""

    def __init__(self, gateway):
        """Initialize the cover."""
        self.pyvlx = gateway
        self._attr_is_on = False
        self.pyvlx.connection.register_connection_opened_cb(self.turn_on)
        self.pyvlx.connection.register_connection_closed_cb(self.turn_off)

    async def turn_on(self):
        """Turn the sensor on."""
        if not self._attr_is_on:
            self._attr_is_on = True
            self.async_write_ha_state()

    async def turn_off(self):
        """Turn the sensor off."""
        if self._attr_is_on:
            self._attr_is_on = False
            self.async_write_ha_state()

    @property
    def name(self):
        """Name of the entity."""
        return "KLF200 Connection State"

    @property
    def device_info(self):
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
        return "KLF200ConnectionState"
