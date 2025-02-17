"""Component to interface with switches that can be controlled remotely."""
import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from pyvlx import OnOffSwitch, OpeningDevice, PyVLX
from pyvlx.opening_device import DualRollerShutter

from .const import DOMAIN, LOGGER
from .node_entity import VeluxNodeEntity

_LOGGER = logging.getLogger(__package__)
PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up sensor(s) for Velux platform."""
    entities: list = []
    pyvlx: PyVLX = hass.data[DOMAIN][entry.entry_id]
    entities.append(VeluxHouseStatusMonitor(pyvlx, entry))
    entities.append(VeluxHeartbeat(pyvlx, entry))
    entities.append(VeluxHeartbeatLoadAllStates(pyvlx, entry))
    for node in pyvlx.nodes:
        if isinstance(node, OnOffSwitch):
            LOGGER.debug("Switch will be added: %s", node.name)
            entities.append(VeluxSwitch(node))
        if isinstance(node, OpeningDevice) and not isinstance(node, DualRollerShutter):
            entities.append(VeluxDefaultVelocityUsedSwitch(node))
    async_add_entities(entities)


class VeluxSwitch(VeluxNodeEntity, SwitchEntity):
    """Representation of a Velux physical switch."""

    def __init__(self, node: OnOffSwitch) -> None:
        """Initialize the switch."""
        super().__init__(node)
        self._attr_device_class = SwitchDeviceClass.SWITCH
        self._attr_is_on = self.node.is_on()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.node.set_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.node.set_off()

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self.node.is_on()



class VeluxDefaultVelocityUsedSwitch(SwitchEntity, RestoreEntity):
    """Representation of a Velux physical switch."""

    def __init__(self, node: OpeningDevice) -> None:
        """Initialize the cover."""
        self.node: OpeningDevice = node
        super().__init__()
        self._attr_unique_id = f"{str(self.node.node_id)}_use_default_velocity"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_device_class = SwitchDeviceClass.SWITCH
        self._attr_name = self.node.name + " Use Default Velocity"
        self._attr_is_on = self.node.use_default_velocity

    async def async_added_to_hass(self) -> None:
        """Restore state from last state."""
        await super().async_added_to_hass()
        s = await self.async_get_last_state()

        LOGGER.info(f"restored value for {self.name}: {str(s)}")  # noqa: G004

        if s is not None and s.state is not None and s.state == "on":
            self.turn_on()
        else:
            self.turn_off()

    @property
    def device_info(self) -> DeviceInfo:
        """Return specific device attributes."""
        return {
            "identifiers": {(DOMAIN, str(self.node.node_id))},
            "name": self.node.name,
        }

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        LOGGER.debug("VeluxDefaultVelocityUsedSwitch: turned on %s", self.node.node_id)
        self.node.use_default_velocity = True

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        LOGGER.debug("VeluxDefaultVelocityUsedSwitch: turned off %s", self.node.node_id)
        self.node.use_default_velocity = False

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self.node.use_default_velocity



class VeluxHouseStatusMonitor(SwitchEntity):
    """Representation of a Velux HouseStatusMonitor switch."""

    def __init__(self, pyvlx: PyVLX, entry: ConfigEntry) -> None:
        """Initialize the switch."""
        self.pyvlx: PyVLX = pyvlx
        self._attr_unique_id = f"{entry.unique_id}_House_Status_Monitor"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_device_class = SwitchDeviceClass.SWITCH
        self._attr_name = "House Status Monitor"
        self._attr_is_on = self.pyvlx.klf200.house_status_monitor_enabled
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.pyvlx.klf200.house_status_monitor_enable(pyvlx=self.pyvlx)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.pyvlx.klf200.house_status_monitor_disable(pyvlx=self.pyvlx)

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self.pyvlx.klf200.house_status_monitor_enabled



class VeluxHeartbeat(SwitchEntity):
    """Representation of a Velux Heartbeat switch."""

    def __init__(self, pyvlx: PyVLX, entry: ConfigEntry) -> None:
        """Initialize the cover."""
        self.pyvlx: PyVLX = pyvlx
        self._attr_unique_id = f"{entry.unique_id}_heartbeat"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_device_class = SwitchDeviceClass.SWITCH
        self._attr_name = "Heartbeat"
        self._attr_is_on = not self.pyvlx.heartbeat.stopped
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
        )

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        self.pyvlx.heartbeat.start()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.pyvlx.heartbeat.stop()

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return not self.pyvlx.heartbeat.stopped



class VeluxHeartbeatLoadAllStates(SwitchEntity):
    """Representation of a VeluxHeartbeatLoadAllStates switch."""

    def __init__(self, pyvlx: PyVLX, entry: ConfigEntry) -> None:
        """Initialize the number entity."""
        self.pyvlx = pyvlx
        self._attr_unique_id = f"{entry.unique_id}_heartbeat_load_all_states"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_device_class = SwitchDeviceClass.SWITCH
        self._attr_name = "Load all states on Heartbeat"
        self._attr_is_on = self.pyvlx.heartbeat.load_all_states
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
        )

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        self.pyvlx.heartbeat.load_all_states = True

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        self.pyvlx.heartbeat.load_all_states = False

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self.pyvlx.heartbeat.load_all_states

