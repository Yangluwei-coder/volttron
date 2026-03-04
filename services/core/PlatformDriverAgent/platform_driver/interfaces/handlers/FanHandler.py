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
        Build and execute the operation on Home Assistant.
        """
        # Validate first
        self.validate(entity_point, value)

        if entity_point == "state":
            # 0 = off, 1 = on
            if value == 1:
                self._call_ha_service(
                    "fan.turn_on",
                    {"entity_id": entity_id}
                )
            else:
                self._call_ha_service(
                    "fan.turn_off",
                    {"entity_id": entity_id}
                )

        elif entity_point == "percentage":
            self._call_ha_service(
                "fan.set_percentage",
                {"entity_id": entity_id, "percentage": value}
            )

        return value
