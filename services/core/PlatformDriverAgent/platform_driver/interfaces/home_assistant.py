# -*- coding: utf-8 -*- {{{
# ===----------------------------------------------------------------------===
#
#                 Component of Eclipse VOLTTRON
#
# ===----------------------------------------------------------------------===
#
# Copyright 2023 Battelle Memorial Institute
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# ===----------------------------------------------------------------------===
# }}}


from abc import ABC, abstractmethod
import random
from math import pi
import json
import sys
from platform_driver.interfaces import BaseInterface, BaseRegister, BasicRevert
from volttron.platform.agent import utils
from volttron.platform.vip.agent import Agent
import logging
import requests
from requests import get

_log = logging.getLogger(__name__)
type_mapping = {"string": str,
                "int": int,
                "integer": int,
                "float": float,
                "bool": bool,
                "boolean": bool}

class HomeAssistantDomainHandler(ABC):
    @abstractmethod
    def validate(self, entity_point, value):
        pass

    @abstractmethod
    def build_operation(self, entity_id, entity_point, value):
        pass
    
class HomeAssistantRegister(BaseRegister):
    def __init__(self, read_only, pointName, units, reg_type, attributes, entity_id, entity_point, default_value=None,
                 description=''):
        super(HomeAssistantRegister, self).__init__("byte", read_only, pointName, units, description='')
        self.reg_type = reg_type
        self.attributes = attributes
        self.entity_id = entity_id
        self.value = None
        self.entity_point = entity_point

class LightHandler(HomeAssistantDomainHandler):
    def validate(self, entity_point, value):
        if entity_point == "state":
            if not (isinstance(value, int) and value in [0, 1]):
                raise ValueError("State value should be an integer value of 1 or 0")
        elif entity_point == "brightness":
            if not (isinstance(value, int) and 0 <= value <= 255):
                raise ValueError("Brightness value should be an integer between 0 and 255")

    def build_operation(self, entity_id, entity_point, value):
        self.validate(entity_point, value)
        service_name = ""
        payload = {"entity_id": entity_id}

        if entity_point == "state":
            service_name = "turn_on" if value == 1 else "turn_off"
        elif entity_point == "brightness":
            service_name = "turn_on"
            payload["brightness"] = value
        
        return {
            "service_domain": "light",
            "service_name": service_name,
            "payload": payload,
            "description": f"set {entity_id} {entity_point} to {value}"
        }

class ClimateHandler(HomeAssistantDomainHandler):
    def __init__(self, units):
        self.units = units

    def validate(self, entity_point, value):
        if entity_point == "state":
            if value not in [0, 2, 3, 4]:
                raise ValueError("Climate state should be an integer value of 0, 2, 3, or 4")

    def build_operation(self, entity_id, entity_point, value):
        self.validate(entity_point, value)
        service_name = ""
        payload = {"entity_id": entity_id}

        if entity_point == "state":
            service_name = "set_hvac_mode"
            mode_map = {0: "off", 2: "heat", 3: "cool", 4: "auto"}
            payload["hvac_mode"] = mode_map[value]
        elif entity_point == "temperature":
            service_name = "set_temperature"
            if self.units == "C":
                value = round((value - 32) * 5/9, 1)
            payload["temperature"] = value

        return {
            "service_domain": "climate",
            "service_name": service_name,
            "payload": payload,
            "description": f"set {entity_id} {entity_point} to {value}"
        }

class InputBooleanHandler(HomeAssistantDomainHandler):
    def validate(self, entity_point, value):
        if not (isinstance(value, int) and value in [0, 1]):
            raise ValueError("InputBoolean state must be 0 or 1")

    def build_operation(self, entity_id, entity_point, value):
        self.validate(entity_point, value)
        service_name = "turn_on" if value == 1 else "turn_off"
        return {
            "service_domain": "input_boolean",
            "service_name": service_name,
            "payload": {"entity_id": entity_id},
            "description": f"set {entity_id} to {service_name}"
        }

def _post_method(url, headers, data, operation_description):
    err = None
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            _log.info(f"Success: {operation_description}")
        else:
            err = f"Failed to {operation_description}. Status code: {response.status_code}. " \
                  f"Response: {response.text}"

    except requests.RequestException as e:
        err = f"Error when attempting - {operation_description} : {e}"
    if err:
        _log.error(err)
        raise Exception(err)


class Interface(BasicRevert, BaseInterface):
    def __init__(self, **kwargs):
        super(Interface, self).__init__(**kwargs)
        self.point_name = None
        self.ip_address = None
        self.access_token = None
        self.port = None
        self.units = None
        self.handler_registry = {}     # Dictionary to hold point names and their corresponding handlers for set_point operations. 

    def configure(self, config_dict, registry_config_str):
        self.ip_address = config_dict.get("ip_address", None)
        self.access_token = config_dict.get("access_token", None)
        self.port = config_dict.get("port", None)

        # Check for None values
        if self.ip_address is None:
            _log.error("IP address is not set.")
            raise ValueError("IP address is required.")
        if self.access_token is None:
            _log.error("Access token is not set.")
            raise ValueError("Access token is required.")
        if self.port is None:
            _log.error("Port is not set.")
            raise ValueError("Port is required.")

        self.parse_config(registry_config_str)

        # Initialize the handler registry with appropriate handlers for different entity types.
        self.handler_registry = {
            "light": LightHandler(),
            "climate": ClimateHandler(self.units),
            "input_boolean": InputBooleanHandler()
        }

    def get_point(self, point_name):
        register = self.get_register_by_name(point_name)

        entity_data = self.get_entity_data(register.entity_id)
        if register.point_name == "state":
            result = entity_data.get("state", None)
            return result
        else:
            value = entity_data.get("attributes", {}).get(f"{register.point_name}", 0)
            return value

    def _set_point(self, point_name, value):
        """
        Issue 3: Implement type validation and conversion based on the register's defined type. This ensures that the value being set is compatible with the expected data type of the Home Assistant entity, preventing errors and ensuring data integrity.
        """
        register = self.get_register_by_name(point_name)
        if register.read_only:
            raise IOError("Trying to write to a point configured read only: " + point_name)
        
        # Type validation and conversion
        register.value = register.reg_type(value)
        
        # get Domain (e.g., 'light.kitchen' -> 'light')
        domain = register.entity_id.split(".")[0]
        
        # Get the appropriate handler based on the domain. If no handler is found, log an error and raise an exception.
        handler = self.handler_registry.get(domain)
        if not handler:
            error_msg = f"Unsupported domain: {domain}. Currently supported: {list(self.handler_registry.keys())}"
            _log.error(error_msg)
            raise ValueError(error_msg)

        # Use the handler to validate the value and build the operation details (service domain, service name, payload).
        operation = handler.build_operation(
            register.entity_id, 
            register.entity_point, 
            register.value
        )

        # Execute the operation by making the appropriate API call to Home Assistant.
        self.execute_service(operation)
        
        return register.value
    
    def execute_service(self, operation):
        """
        Executes a Home Assistant service call based on the provided operation details.
        """
        url = f"http://{self.ip_address}:{self.port}/api/services/{operation['service_domain']}/{operation['service_name']}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        _post_method(url, headers, operation['payload'], operation['description'])

    def get_entity_data(self, point_name):
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        # the /states grabs current state AND attributes of a specific entity
        url = f"http://{self.ip_address}:{self.port}/api/states/{point_name}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()  # return the json attributes from entity
        else:
            error_msg = f"Request failed with status code {response.status_code}, Point name: {point_name}, " \
                        f"response: {response.text}"
            _log.error(error_msg)
            raise Exception(error_msg)

    def _scrape_all(self):
        result = {}
        read_registers = self.get_registers_by_type("byte", True)
        write_registers = self.get_registers_by_type("byte", False)

        for register in read_registers + write_registers:
            entity_id = register.entity_id
            entity_point = register.entity_point
            try:
                entity_data = self.get_entity_data(entity_id)  # Using Entity ID to get data
                if "climate." in entity_id:  # handling thermostats.
                    if entity_point == "state":
                        state = entity_data.get("state", None)
                        # Giving thermostat states an equivalent number.
                        if state == "off":
                            register.value = 0
                            result[register.point_name] = 0
                        elif state == "heat":
                            register.value = 2
                            result[register.point_name] = 2
                        elif state == "cool":
                            register.value = 3
                            result[register.point_name] = 3
                        elif state == "auto":
                            register.value = 4
                            result[register.point_name] = 4
                        else:
                            error_msg = f"State {state} from {entity_id} is not yet supported"
                            _log.error(error_msg)
                            ValueError(error_msg)
                    # Assigning attributes
                    else:
                        attribute = entity_data.get("attributes", {}).get(f"{entity_point}", 0)
                        register.value = attribute
                        result[register.point_name] = attribute
                # handling light states
                elif "light." or "input_boolean." in entity_id: # Checks for lights or input bools since they have the same states.
                    if entity_point == "state":
                        state = entity_data.get("state", None)
                        # Converting light states to numbers.
                        if state == "on":
                            register.value = 1
                            result[register.point_name] = 1
                        elif state == "off":
                            register.value = 0
                            result[register.point_name] = 0
                    else:
                        attribute = entity_data.get("attributes", {}).get(f"{entity_point}", 0)
                        register.value = attribute
                        result[register.point_name] = attribute
                else:  # handling all devices that are not thermostats or light states
                    if entity_point == "state":

                        state = entity_data.get("state", None)
                        register.value = state
                        result[register.point_name] = state
                    # Assigning attributes
                    else:
                        attribute = entity_data.get("attributes", {}).get(f"{entity_point}", 0)
                        register.value = attribute
                        result[register.point_name] = attribute
            except Exception as e:
                _log.error(f"An unexpected error occurred for entity_id: {entity_id}: {e}")

        return result

    def parse_config(self, config_dict):

        if config_dict is None:
            return
        for regDef in config_dict:

            if not regDef['Entity ID']:
                continue

            read_only = str(regDef.get('Writable', '')).lower() != 'true'
            entity_id = regDef['Entity ID']
            entity_point = regDef['Entity Point']
            self.point_name = regDef['Volttron Point Name']
            self.units = regDef['Units']
            description = regDef.get('Notes', '')
            default_value = ("Starting Value")
            type_name = regDef.get("Type", 'string')
            reg_type = type_mapping.get(type_name, str)
            attributes = regDef.get('Attributes', {})
            register_type = HomeAssistantRegister

            register = register_type(
                read_only,
                self.point_name,
                self.units,
                reg_type,
                attributes,
                entity_id,
                entity_point,
                default_value=default_value,
                description=description)

            if default_value is not None:
                self.set_default(self.point_name, register.value)

            self.insert_register(register)
