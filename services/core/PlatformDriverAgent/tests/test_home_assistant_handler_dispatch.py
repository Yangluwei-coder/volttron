import pytest

from platform_driver.interfaces.home_assistant import Interface
from platform_driver.interfaces.handlers.FanHandler import FanHandler


class _DummyRegister:
    def __init__(self, entity_id, entity_point, reg_type=int, read_only=False):
        self.entity_id = entity_id
        self.entity_point = entity_point
        self.reg_type = reg_type
        self.read_only = read_only
        self.value = None


@pytest.mark.driver_unit
# Verifies fan writes follow canary dispatch and generate the expected normalized operation.
def test_set_point_fan_success_dispatches_operation():
    interface = Interface()
    register = _DummyRegister(entity_id="fan.office_fan", entity_point="state")

    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"fan": FanHandler()}

    captured = {}

    def _fake_execute_service(operation):
        captured["operation"] = operation

    interface._execute_service = _fake_execute_service

    result = interface._set_point("fan_state", 1)

    assert result == 1
    assert register.value == 1
    assert captured["operation"]["service_domain"] == "fan"
    assert captured["operation"]["service_name"] == "turn_on"
    assert captured["operation"]["payload"] == {"entity_id": "fan.office_fan"}

@pytest.mark.driver_unit
# Verifies fan percentage writes map to set_percentage with correct payload.
def test_set_point_fan_percentage_dispatches_operation():
    interface = Interface()
    register = _DummyRegister(entity_id="fan.office_fan", entity_point="percentage")

    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"fan": FanHandler()}

    captured = {}

    def _fake_execute_service(operation):
        captured["operation"] = operation

    interface._execute_service = _fake_execute_service

    result = interface._set_point("fan_percentage", 60)

    assert result == 60
    assert register.value == 60
    assert captured["operation"]["service_domain"] == "fan"
    assert captured["operation"]["service_name"] == "set_percentage"
    assert captured["operation"]["payload"] == {
        "entity_id": "fan.office_fan",
        "percentage": 60,
    }
    
@pytest.mark.driver_unit
# Verifies safe failure when fan domain is routed but handler is not registered.
def test_set_point_fan_missing_handler_raises_meaningful_error():
    interface = Interface()
    register = _DummyRegister(entity_id="fan.office_fan", entity_point="state")

    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {}

    with pytest.raises(ValueError, match="Missing 'fan' handler"):
        interface._set_point("fan_state", 1)


@pytest.mark.driver_unit
# Verifies unsupported/unknown domains fail with a clear error (no silent fallback).
def test_set_point_unknown_device_raises_meaningful_error():
    interface = Interface()
    register = _DummyRegister(entity_id="unknown_device.xyz", entity_point="state")

    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"fan": FanHandler()}

    with pytest.raises(ValueError, match="Unsupported entity_id"):
        interface._set_point("unknown_point", 1)