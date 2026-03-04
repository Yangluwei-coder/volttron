import logging
import requests

from .base import HomeAssistantDomainHandler

_log = logging.getLogger(__name__)


class FanHandler(HomeAssistantDomainHandler):
    """
    Handler for Home Assistant fan.
    """

    def __init__(self, config=None):
        super().__init__(config)
        self.interface = None

    def set_interface(self, interface):
        self.interface = interface

    # TODO(issue-40): Deprecate this method after migrating all handlers to build_operation.
    def _call_ha_service(self, service, service_data):
        """Call Home Assistant API service"""
        url = f"http://{self.interface.ip_address}:{self.interface.port}" \
              f"/api/services/{service}"
        headers = {
            "Authorization": f"Bearer {self.interface.access_token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url, headers=headers, json=service_data)
            if response.status_code == 200:
                _log.info(f"Success: {service} with {service_data}")
            else:
                error_msg = f"Failed to {service}. Status: " \
                            f"{response.status_code}, Response: " \
                            f"{response.text}"
                raise Exception(error_msg)
        except requests.RequestException as e:
            error_msg = f"Error calling {service}: {e}"
            raise Exception(error_msg)

    def validate(self, entity_point, value):
        """
        Validate the value to be set on the entity point.       
        """
        if entity_point == "state":
            if not isinstance(value, int) or value not in [0, 1]:
                error_msg = f"Fan state value must be integer 0 (off) or " \
                            f"1 (on), got: {value}"
                _log.error(error_msg)
                raise ValueError(error_msg)

        elif entity_point == "percentage":
            if not isinstance(value, (int, float)) or not (0 <= value <= 100):
                error_msg = f"Fan percentage must be between 0 and 100, " \
                            f"got: {value}"
                _log.error(error_msg)
                raise ValueError(error_msg)

        else:
            error_msg = f"Unsupported entity_point for fan: {entity_point}. " \
                        f"Supported: state, percentage"
            _log.error(error_msg)
            raise ValueError(error_msg)

        return True

    def build_operation(self, entity_id, entity_point, value):
        """
        Validate fan write input and return normalized operation descriptor.
        """
        self.validate(entity_point, value)

        if entity_point == "state":
            service_name = "turn_on" if value == 1 else "turn_off"
            return {
                "service_domain": "fan",
                "service_name": service_name,
                "payload": {"entity_id": entity_id},
                "description": f"set {entity_id} state to {value}",
            }

        if entity_point == "percentage":
            return {
                "service_domain": "fan",
                "service_name": "set_percentage",
                "payload": {"entity_id": entity_id, "percentage": value},
                "description": f"set {entity_id} percentage to {value}",
            }

        # Defensive fallback; validate should already catch unsupported points.
        raise ValueError(f"Unsupported fan entity_point: {entity_point}")
