# -*- coding: utf-8 -*-
"""
Standalone live integration tests for Home Assistant fan entity.
Does NOT require a running VOLTTRON instance — calls HA REST API directly.

Run:
    export HOMEASSISTANT_TEST_IP="localhost"
    export ACCESS_TOKEN="your_token"
    export PORT="8123"
    python -m pytest services/core/PlatformDriverAgent/tests/test_ha_fan_live.py -v
"""

import os
import time
import pytest
import requests

HA_IP = os.environ.get("HOMEASSISTANT_TEST_IP", "")
TOKEN = os.environ.get("ACCESS_TOKEN", "")
PORT = os.environ.get("PORT", "8123")

skip_if_no_env = pytest.mark.skipif(
    not (HA_IP and TOKEN and PORT),
    reason="Requires HOMEASSISTANT_TEST_IP, ACCESS_TOKEN, PORT"
)


def headers():
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    }


def call_service(domain, service, entity_id, extra=None):
    payload = {"entity_id": entity_id}
    if extra:
        payload.update(extra)
    url = f"http://{HA_IP}:{PORT}/api/services/{domain}/{service}"
    resp = requests.post(url, headers=headers(), json=payload)
    assert resp.status_code == 200, f"Service call failed: {resp.text}"


def get_state(entity_id):
    url = f"http://{HA_IP}:{PORT}/api/states/{entity_id}"
    resp = requests.get(url, headers=headers())
    assert resp.status_code == 200, f"State fetch failed: {resp.text}"
    return resp.json()


@pytest.fixture(autouse=True)
def reset_fan():
    yield
    call_service("fan", "turn_off", "fan.volttron_test_fan")
    call_service("input_number", "set_value", "input_number.fan_speed", extra={"value": 0})
    time.sleep(0.5)


@skip_if_no_env
def test_fan_get_point():
    """get_point: reading fan state returns expected value."""
    call_service("fan", "turn_off", "fan.volttron_test_fan")
    time.sleep(0.5)
    state = get_state("fan.volttron_test_fan")
    assert state["state"] == "off"


@skip_if_no_env
def test_fan_set_point_on():
    """set_point state on: value 1 turns fan on."""
    call_service("fan", "turn_on", "fan.volttron_test_fan")
    time.sleep(0.5)
    state = get_state("fan.volttron_test_fan")
    assert state["state"] == "on"


@skip_if_no_env
def test_fan_set_point_off():
    """set_point state off: value 0 turns fan off."""
    call_service("fan", "turn_on", "fan.volttron_test_fan")
    time.sleep(0.5)
    call_service("fan", "turn_off", "fan.volttron_test_fan")
    time.sleep(0.5)
    state = get_state("fan.volttron_test_fan")
    assert state["state"] == "off"


@skip_if_no_env
def test_fan_set_point_percentage():
    """set_point percentage: sets fan speed correctly."""
    call_service("fan", "turn_on", "fan.volttron_test_fan")
    time.sleep(0.5)
    call_service("fan", "set_percentage", "fan.volttron_test_fan", extra={"percentage": 60})
    time.sleep(0.5)
    speed = get_state("input_number.fan_speed")
    assert float(speed["state"]) == 60.0


@skip_if_no_env
def test_fan_scrape_all():
    """scrape_all: fan points appear in results."""
    call_service("fan", "turn_on", "fan.volttron_test_fan")
    time.sleep(0.5)
    fan_state = get_state("fan.volttron_test_fan")
    fan_speed = get_state("input_number.fan_speed")
    assert "state" in fan_state
    assert "state" in fan_speed
    assert fan_state["state"] == "on"