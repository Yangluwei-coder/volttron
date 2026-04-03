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

import json
import logging
import pytest
import gevent
import os

from volttron.platform.agent.known_identities import (
    PLATFORM_DRIVER,
    CONFIGURATION_STORE,
)
from volttron.platform import get_services_core
from volttron.platform.agent import utils
from volttron.platform.keystore import KeyStore
from volttrontesting.utils.platformwrapper import PlatformWrapper

utils.setup_logging()
logger = logging.getLogger(__name__)

# To run these tests, create a helper toggle named volttrontest in your Home Assistant instance.
# This can be done by going to Settings > Devices & services > Helpers > Create Helper > Toggle
HOMEASSISTANT_TEST_IP = os.environ.get("HOMEASSISTANT_TEST_IP", "")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "")
PORT = os.environ.get("PORT", "")

skip_msg = "Some configuration variables are not set. Check HOMEASSISTANT_TEST_IP, ACCESS_TOKEN, and PORT"

# Skip tests if variables are not set
pytestmark = pytest.mark.skipif(
    not (HOMEASSISTANT_TEST_IP and ACCESS_TOKEN and PORT),
    reason=skip_msg
)
HOMEASSISTANT_DEVICE_TOPIC = "devices/home_assistant"

# TODO: this is a separate Platform Driver device used only for fan tests.
# One HA connection could use a single devices/home_assistant topic with a combined registry; 
# the split is for current test/fixture layout (e.g. fan_config_store teardown)
# and may be consolidated when adding light/climate or refactor fixtures.
HOMEASSISTANT_FAN_TOPIC = "devices/home_assistant_fan"


# ---------------------------------------------------------------------------
# input_boolean tests (existing)
# ---------------------------------------------------------------------------

def test_get_point(volttron_instance, config_store):
    expected_values = 0
    agent = volttron_instance.dynamic_agent
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'bool_state').get(timeout=20)
    assert result == expected_values, "The result does not match the expected result."


def test_data_poll(volttron_instance: PlatformWrapper, config_store):
    expected_values = [{'bool_state': 0}, {'bool_state': 1}]
    agent = volttron_instance.dynamic_agent
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'scrape_all', 'home_assistant').get(timeout=20)
    assert result in expected_values, "The result does not match the expected result."


def test_set_point(volttron_instance, config_store):
    expected_values = {'bool_state': 1}
    agent = volttron_instance.dynamic_agent
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'bool_state', 1)
    gevent.sleep(10)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'scrape_all', 'home_assistant').get(timeout=20)
    assert result == expected_values, "The result does not match the expected result."


# ---------------------------------------------------------------------------
# Fan tests (new) — satisfies TODO(#41)
# ---------------------------------------------------------------------------

def test_fan_get_point(volttron_instance, fan_config_store):
    """Fan get_point returns expected state value (1 or 0)."""
    agent = volttron_instance.dynamic_agent
    result = agent.vip.rpc.call(
        PLATFORM_DRIVER, 'get_point', 'home_assistant_fan', 'fan_state'
    ).get(timeout=20)
    assert result in (1, 0), f"Unexpected fan state: {result}"


def test_fan_set_point_on(volttron_instance, fan_config_store):
    """set_point with value 1 turns fan on."""
    agent = volttron_instance.dynamic_agent
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant_fan', 'fan_state', 1).get(timeout=20)
    gevent.sleep(2)
    result = agent.vip.rpc.call(
        PLATFORM_DRIVER, 'get_point', 'home_assistant_fan', 'fan_state'
    ).get(timeout=20)
    assert result == 1, f"Expected fan to be 'on', got: {result}"


def test_fan_set_point_off(volttron_instance, fan_config_store):
    """set_point with value 0 turns fan off."""
    agent = volttron_instance.dynamic_agent
    # Turn on first to ensure we're testing the off transition
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant_fan', 'fan_state', 1).get(timeout=20)
    gevent.sleep(2)
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant_fan', 'fan_state', 0).get(timeout=20)
    gevent.sleep(2)
    result = agent.vip.rpc.call(
        PLATFORM_DRIVER, 'get_point', 'home_assistant_fan', 'fan_state'
    ).get(timeout=20)
    assert result == 0, f"Expected fan to be 'off', got: {result}"


def test_fan_set_point_percentage(volttron_instance, fan_config_store):
    """set_point with percentage value sets fan speed correctly."""
    agent = volttron_instance.dynamic_agent
    # Turn fan on first — percentage only works when fan is on
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant_fan', 'fan_state', 1).get(timeout=20)
    gevent.sleep(2)
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant_fan', 'fan_percentage', 60).get(timeout=20)
    gevent.sleep(2)
    result = agent.vip.rpc.call(
        PLATFORM_DRIVER, 'get_point', 'home_assistant_fan', 'fan_percentage'
    ).get(timeout=20)
    assert float(result) == 60.0, f"Expected fan percentage 60, got: {result}"


def test_fan_scrape_all(volttron_instance, fan_config_store):
    """Fan points appear in scrape_all results."""
    agent = volttron_instance.dynamic_agent
    result = agent.vip.rpc.call(
        PLATFORM_DRIVER, 'scrape_all', 'home_assistant_fan'
    ).get(timeout=20)
    assert 'fan_state' in result, f"fan_state missing from scrape_all: {result}"
    assert 'fan_percentage' in result, f"fan_percentage missing from scrape_all: {result}"


# ---------------------------------------------------------------------------
# Fixtures — input_boolean (existing)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def config_store(volttron_instance, platform_driver):
    capabilities = [{"edit_config_store": {"identity": PLATFORM_DRIVER}}]
    volttron_instance.add_capabilities(volttron_instance.dynamic_agent.core.publickey, capabilities)

    registry_config = "homeassistant_test.json"
    registry_obj = [{
        "Entity ID": "input_boolean.volttrontest",
        "Entity Point": "state",
        "Volttron Point Name": "bool_state",
        "Units": "On / Off",
        "Units Details": "off: 0, on: 1",
        "Writable": True,
        "Starting Value": 3,
        "Type": "int",
        "Notes": "lights hallway"
    }]

    volttron_instance.dynamic_agent.vip.rpc.call(CONFIGURATION_STORE,
                                                 "manage_store",
                                                 PLATFORM_DRIVER,
                                                 registry_config,
                                                 json.dumps(registry_obj),
                                                 config_type="json")
    gevent.sleep(2)

    driver_config = {
        "driver_config": {"ip_address": HOMEASSISTANT_TEST_IP, "access_token": ACCESS_TOKEN, "port": PORT},
        "driver_type": "home_assistant",
        "registry_config": f"config://{registry_config}",
        "timezone": "US/Pacific",
        "interval": 30,
    }

    volttron_instance.dynamic_agent.vip.rpc.call(CONFIGURATION_STORE,
                                                 "manage_store",
                                                 PLATFORM_DRIVER,
                                                 HOMEASSISTANT_DEVICE_TOPIC,
                                                 json.dumps(driver_config),
                                                 config_type="json")
    gevent.sleep(2)
    yield platform_driver

    print("Wiping out store.")
    volttron_instance.dynamic_agent.vip.rpc.call(CONFIGURATION_STORE, "manage_delete_store", PLATFORM_DRIVER)
    gevent.sleep(0.1)


# ---------------------------------------------------------------------------
# Fixtures — fan (new)
# ---------------------------------------------------------------------------

@pytest.fixture()
def fan_config_store(volttron_instance, platform_driver):
    """
    Register fan.volttron_test_fan (state + percentage) in the config store.
    Tears down and resets fan helpers after each test.
    """
    capabilities = [{"edit_config_store": {"identity": PLATFORM_DRIVER}}]
    volttron_instance.add_capabilities(volttron_instance.dynamic_agent.core.publickey, capabilities)

    registry_config = "homeassistant_fan_test.json"
    registry_obj = [
        {
            "Entity ID": "fan.volttron_test_fan",
            "Entity Point": "state",
            "Volttron Point Name": "fan_state",
            "Units": "On / Off",
            "Units Details": "off: 0, on: 1",
            "Writable": True,
            "Starting Value": 0,
            "Type": "int",
            "Notes": "fan state"
        },
        {
            "Entity ID": "fan.volttron_test_fan",
            "Entity Point": "percentage",
            "Volttron Point Name": "fan_percentage",
            "Units": "%",
            "Units Details": "0-100",
            "Writable": True,
            "Starting Value": 0,
            "Type": "float",
            "Notes": "fan speed percentage"
        },
    ]

    volttron_instance.dynamic_agent.vip.rpc.call(CONFIGURATION_STORE,
                                                 "manage_store",
                                                 PLATFORM_DRIVER,
                                                 registry_config,
                                                 json.dumps(registry_obj),
                                                 config_type="json")
    gevent.sleep(2)

    driver_config = {
        "driver_config": {"ip_address": HOMEASSISTANT_TEST_IP, "access_token": ACCESS_TOKEN, "port": PORT},
        "driver_type": "home_assistant",
        "registry_config": f"config://{registry_config}",
        "timezone": "US/Pacific",
        "interval": 30,
    }

    volttron_instance.dynamic_agent.vip.rpc.call(CONFIGURATION_STORE,
                                                 "manage_store",
                                                 PLATFORM_DRIVER,
                                                 HOMEASSISTANT_FAN_TOPIC,
                                                 json.dumps(driver_config),
                                                 config_type="json")
    gevent.sleep(2)

    yield platform_driver

    # --- teardown: reset fan helpers to known state ---
    try:
        agent = volttron_instance.dynamic_agent
        agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant_fan', 'fan_state', 0).get(timeout=10)
        gevent.sleep(1)
    except Exception as e:
        logger.warning(f"Fan teardown reset failed: {e}")

    volttron_instance.dynamic_agent.vip.rpc.call(CONFIGURATION_STORE,
                                                 "manage_delete_store",
                                                 PLATFORM_DRIVER)
    gevent.sleep(0.1)


@pytest.fixture(scope="module")
def platform_driver(volttron_instance):
    platform_uuid = volttron_instance.install_agent(
        agent_dir=get_services_core("PlatformDriverAgent"),
        config_file={
            "publish_breadth_first_all": False,
            "publish_depth_first": False,
            "publish_breadth_first": False,
        },
        start=True,
    )
    gevent.sleep(2)
    assert volttron_instance.is_agent_running(platform_uuid)
    yield platform_uuid

    volttron_instance.stop_agent(platform_uuid)
    if not volttron_instance.debug_mode:
        volttron_instance.remove_agent(platform_uuid)