import logging
from .base import HomeAssistantDomainHandler

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
        service = "turn_on" if value == 1 else "turn_off"
        return {
            "service_domain": "input_boolean",
            "service_name": service,
            "payload": {"entity_id": entity_id},
            "description": f"{service} input_boolean {entity_id}"
        }
