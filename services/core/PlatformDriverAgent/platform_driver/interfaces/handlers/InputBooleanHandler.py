import logging
from .base import HomeAssistantDomainHandler, ha_on_off_state_to_volttron

_log = logging.getLogger(__name__)

class InputBooleanHandler(HomeAssistantDomainHandler):
    def __init__(self, config=None):
        super().__init__(config)
        self.interface = None
        self.supported_points = ["state"]

    def set_interface(self, interface):
        self.interface = interface

    def validate(self, entity_point, value):
        if entity_point != "state":
            raise ValueError("InputBoolean only supports 'state' point")
        if value not in [0, 1]:
            raise ValueError(f"InputBoolean value must be 0 or 1, got: {value}")
        return True

    def build_operation(self, entity_id, entity_point, value):
        self.validate(entity_point, value)
        # input_boolean only has toggle service, not turn_on/turn_off.
        return {
            "service_domain": "input_boolean",
            "service_name": "toggle",
            "payload": {"entity_id": entity_id},
            "description": f"toggle input_boolean {entity_id}"
        }

    def normalize_read_state(self, entity_point, raw_state):
        if entity_point == "state":
            return ha_on_off_state_to_volttron(raw_state)
        return super().normalize_read_state(entity_point, raw_state)
