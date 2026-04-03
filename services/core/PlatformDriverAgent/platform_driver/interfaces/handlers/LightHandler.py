import logging
from .base import HomeAssistantDomainHandler, ha_on_off_state_to_volttron

_log = logging.getLogger(__name__)

class LightHandler(HomeAssistantDomainHandler):
    def __init__(self, config=None):
        super().__init__(config)
        self.interface = None
        self.supported_points = ["state", "brightness"]

    def set_interface(self, interface):
        self.interface = interface

    def validate(self, entity_point, value):
        if entity_point == "state":
            if not isinstance(value, int) or value not in [0, 1]:
                raise ValueError(f"Light state must be 0 or 1, got: {value}")
        elif entity_point == "brightness":
            if not isinstance(value, int) or not (0 <= value <= 255):
                raise ValueError(f"Brightness must be 0-255, got: {value}")
        else:
            raise ValueError(f"Unsupported light point: {entity_point}")
        return True

    def build_operation(self, entity_id, entity_point, value):
        self.validate(entity_point, value)
        
        if entity_point == "state":
            service = "turn_on" if value == 1 else "turn_off"
            return {
                "service_domain": "light",
                "service_name": service,
                "payload": {"entity_id": entity_id},
                "description": f"{service} light {entity_id}"
            }
        
        if entity_point == "brightness":
            return {
                "service_domain": "light",
                "service_name": "turn_on",
                "payload": {"entity_id": entity_id, "brightness": value},
                "description": f"set {entity_id} brightness to {value}"
            }

    def normalize_read_state(self, entity_point, raw_state):
        if entity_point == "state":
            return ha_on_off_state_to_volttron(raw_state)
        return super().normalize_read_state(entity_point, raw_state)
