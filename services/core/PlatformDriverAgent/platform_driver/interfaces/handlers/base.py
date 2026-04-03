from abc import ABC, abstractmethod

def ha_on_off_state_to_volttron(raw_state):
    """Map HA binary entity state strings to Volttron 0/1; leave other values unchanged (e.g. unavailable, unknown)."""
    if raw_state == "on":
        return 1
    if raw_state == "off":
        return 0
    return raw_state

class HomeAssistantDomainHandler(ABC):
    def __init__(self, config=None):
        self.config = config

    @abstractmethod
    def validate(self, entity_point, value):
        """subclass must implement validation logic for the value to be set on the entity point"""
        pass

    @abstractmethod
    def build_operation(self, entity_id, entity_point, value):
        pass

    def normalize_read_state(self, entity_point, raw_state):
        """Return Volttron-facing value for a raw HA state string. Default: pass-through."""
        return raw_state
