import logging
from .base import HomeAssistantDomainHandler

_log = logging.getLogger(__name__)

class ClimateHandler(HomeAssistantDomainHandler):
    # 映射逻辑保持与你原代码一致
    MODE_MAP = {0: "off", 2: "heat", 3: "cool", 4: "auto"}

    def __init__(self, config=None):
        super().__init__(config)
        self.interface = None

    def set_interface(self, interface):
        self.interface = interface

    def validate(self, entity_point, value):
        if entity_point == "state":
            if value not in self.MODE_MAP:
                raise ValueError(f"Climate state must be 0, 2, 3, or 4, got: {value}")
        elif entity_point == "temperature":
            if not isinstance(value, (int, float)):
                raise ValueError(f"Temperature must be numeric, got: {value}")
        return True

    def build_operation(self, entity_id, entity_point, value):
        self.validate(entity_point, value)

        if entity_point == "state":
            return {
                "service_domain": "climate",
                "service_name": "set_hvac_mode",
                "payload": {"entity_id": entity_id, "hvac_mode": self.MODE_MAP[value]},
                "description": f"set {entity_id} mode to {self.MODE_MAP[value]}"
            }

        if entity_point == "temperature":
            # 自动处理摄氏度转换逻辑（如果 interface 标记为 'C'）
            target_temp = value
            if getattr(self.interface, 'units', 'F') == "C":
                target_temp = round((value - 32) * 5/9, 1)
            
            return {
                "service_domain": "climate",
                "service_name": "set_temperature",
                "payload": {"entity_id": entity_id, "temperature": target_temp},
                "description": f"set {entity_id} temp to {target_temp}"
            }
