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


import random
from math import pi
import json
import sys
from platform_driver.interfaces import BaseInterface, BaseRegister, BasicRevert
from platform_driver.interfaces.handlers import get_handler_registry
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


class HomeAssistantRegister(BaseRegister):
    def __init__(self, read_only, pointName, units, reg_type, attributes, entity_id, entity_point, default_value=None, description=''):
        super(HomeAssistantRegister, self).__init__("byte", read_only, pointName, units, description=description)
        self.reg_type = reg_type
        self.attributes = attributes
        self.entity_id = entity_id
        self.entity_point = entity_point
        self.value = None

class Interface(BasicRevert, BaseInterface):
    def __init__(self, **kwargs):
        super(Interface, self).__init__(**kwargs)
        self.ip_address = None
        self.access_token = None
        self.port = None
        self.units = "F"
        # Initialize domain-to-handler registry for write dispatch.
        self.handler_registry = get_handler_registry()

    def configure(self, config_dict, registry_config_str):
        self.ip_address = config_dict.get("ip_address", None)
        self.access_token = config_dict.get("access_token", None)
        self.port = config_dict.get("port", None)
        self.units = config_dict.get("units", "F")
        
        if not all([self.ip_address, self.access_token, self.port]):
            _log.error("Missing HA connection configuration (IP, Token, or Port)")
            raise ValueError("Configuration requires ip_address, access_token, and port")

        self.parse_config(registry_config_str)

    def _set_point(self, point_name, value):
        register = self.get_register_by_name(point_name)
        if register.read_only:
            raise IOError(f"Point {point_name} is read-only")

        register.value = register.reg_type(value)
        
        domain = register.entity_id.split(".", 1)[0]
        
        handler = self.handler_registry.get(domain)
        
        if not handler:
            supported_domains = set(get_handler_registry().keys())
            if domain in supported_domains:
                raise ValueError(f"Missing '{domain}' handler in registry.")
            else:
                raise ValueError(f"Unsupported entity_id domain: {domain}.")

        if hasattr(handler, "set_interface"):
            handler.set_interface(self)

        try:
            operation = handler.build_operation(
                register.entity_id, 
                register.entity_point, 
                register.value
            )
            self._execute_service(operation)
            return register.value
        except Exception as e:
            _log.error(f"Error setting point {point_name}: {e}")
            raise
    
    def _execute_service(self, operation):
        """
        Execute normalized HA service operation descriptor.
        Expected keys: service_domain, service_name, payload, description
        """
        # Compose unified Home Assistant API service URL.
        url = f"http://{self.ip_address}:{self.port}/api/services/{operation['service_domain']}/{operation['service_name']}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        
        try:
            response = requests.post(url, headers=headers, json=operation["payload"])
            if response.status_code == 200:
                _log.info(f"Successfully executed: {operation['description']}")
            else:
                _log.error(f"HA Error {response.status_code}: {response.text}")
                raise Exception(f"Home Assistant service call failed: {response.text}")
        except requests.RequestException as e:
            _log.error(f"Network error calling HA API: {e}")
            raise

    def get_point(self, point_name):
        register = self.get_register_by_name(point_name)
        entity_data = self.get_entity_data(register.entity_id)
        
        if register.entity_point == "state":
            return entity_data.get("state")
        return entity_data.get("attributes", {}).get(register.entity_point, 0)

    def get_entity_data(self, entity_id):
        url = f"http://{self.ip_address}:{self.port}/api/states/{entity_id}"
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        raise Exception(f"Failed to fetch {entity_id}: {response.status_code}")

    def parse_config(self, config_dict):
        if not config_dict:
            return
        for regDef in config_dict:
            if not regDef.get('Entity ID'):
                continue

            read_only = str(regDef.get('Writable', '')).lower() != 'true'
            type_name = regDef.get("Type", 'string')
            
            register = HomeAssistantRegister(
                read_only=read_only,
                pointName=regDef['Volttron Point Name'],
                units=regDef.get('Units', ''),
                reg_type=type_mapping.get(type_name, str),
                attributes=regDef.get('Attributes', {}),
                entity_id=regDef['Entity ID'],
                entity_point=regDef['Entity Point'],
                description=regDef.get('Notes', '')
            )
            self.insert_register(register)

    def _scrape_all(self):
        result = {}
        for register in self.registers:
            try:
                val = self.get_point(register.point_name)
                result[register.point_name] = val
            except Exception as e:
                _log.warning(f"Could not scrape {register.point_name}: {e}")
        return result

    
