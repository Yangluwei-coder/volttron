import pytest

from platform_driver.interfaces.home_assistant import Interface
from platform_driver.interfaces.handlers.FanHandler import FanHandler
from platform_driver.interfaces.handlers.LightHandler import LightHandler
from platform_driver.interfaces.handlers.ClimateHandler import ClimateHandler
from platform_driver.interfaces.handlers.InputBooleanHandler import InputBooleanHandler

class _DummyRegister:
    def __init__(self, entity_id, entity_point, reg_type=int, read_only=False):
        self.entity_id = entity_id
        self.entity_point = entity_point
        self.reg_type = reg_type
        self.read_only = read_only
        self.value = None

# ---------- Fan Handler tests ----------

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

    with pytest.raises(ValueError, match="Missing 'fan' handler in registry."):
        interface._set_point("fan_state", 1)

@pytest.mark.driver_unit
# Verifies unsupported/unknown domains fail with a clear error (no silent fallback).
def test_set_point_unknown_device_raises_meaningful_error():
    interface = Interface()
    register = _DummyRegister(entity_id="unknown_device.xyz", entity_point="state")

    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"fan": FanHandler()}

    with pytest.raises(ValueError, match="Unsupported entity_id domain: unknown_device."):
        interface._set_point("unknown_point", 1)

@pytest.mark.driver_unit
# Verifies fan state off dispatches turn_off operation.
def test_set_point_fan_state_off_dispatches_operation():
    interface = Interface()
    register = _DummyRegister(entity_id="fan.office_fan", entity_point="state")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"fan": FanHandler()}
    captured = {}
    def _fake_execute_service(operation):
        captured["operation"] = operation
    interface._execute_service = _fake_execute_service
    result = interface._set_point("fan_state", 0)
    assert result == 0
    assert register.value == 0
    assert captured["operation"]["service_domain"] == "fan"
    assert captured["operation"]["service_name"] == "turn_off"
    assert captured["operation"]["payload"] == {"entity_id": "fan.office_fan"}

@pytest.mark.driver_unit
# Verifies fan state out of range is rejected.
def test_set_point_fan_state_out_of_range_raises_error():
    interface = Interface()
    register = _DummyRegister(entity_id="fan.office_fan", entity_point="state")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"fan": FanHandler()}
    with pytest.raises(ValueError, match="Fan state value must be integer 0"):
        interface._set_point("fan_state", 2)

@pytest.mark.driver_unit
# Verifies fan percentage at lower boundary (0) is accepted.
def test_set_point_fan_percentage_at_lower_bound():
    interface = Interface()
    register = _DummyRegister(entity_id="fan.office_fan", entity_point="percentage")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"fan": FanHandler()}
    captured = {}
    def _fake_execute_service(operation):
        captured["operation"] = operation
    interface._execute_service = _fake_execute_service
    result = interface._set_point("fan_percentage", 0)
    assert result == 0
    assert captured["operation"]["payload"] == {"entity_id": "fan.office_fan", "percentage": 0}

@pytest.mark.driver_unit
# Verifies fan percentage at upper boundary (100) is accepted.
def test_set_point_fan_percentage_at_upper_bound():
    interface = Interface()
    register = _DummyRegister(entity_id="fan.office_fan", entity_point="percentage")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"fan": FanHandler()}
    captured = {}
    def _fake_execute_service(operation):
        captured["operation"] = operation
    interface._execute_service = _fake_execute_service
    result = interface._set_point("fan_percentage", 100)
    assert result == 100
    assert captured["operation"]["payload"] == {"entity_id": "fan.office_fan", "percentage": 100}

@pytest.mark.driver_unit
# Verifies fan percentage above 100 is rejected.
def test_set_point_fan_percentage_above_range_raises_error():
    interface = Interface()
    register = _DummyRegister(entity_id="fan.office_fan", entity_point="percentage")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"fan": FanHandler()}
    with pytest.raises(ValueError, match="Fan percentage must be between 0 and 100"):
        interface._set_point("fan_percentage", 101)

@pytest.mark.driver_unit
# Verifies fan percentage below 0 is rejected.
def test_set_point_fan_percentage_below_range_raises_error():
    interface = Interface()
    register = _DummyRegister(entity_id="fan.office_fan", entity_point="percentage")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"fan": FanHandler()}
    with pytest.raises(ValueError, match="Fan percentage must be between 0 and 100"):
        interface._set_point("fan_percentage", -1)

@pytest.mark.driver_unit
# Verifies non-numeric fan percentage is rejected.
def test_set_point_fan_percentage_non_numeric_raises_error():
    interface = Interface()
    register = _DummyRegister(entity_id="fan.office_fan", entity_point="percentage", reg_type=str)
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"fan": FanHandler()}
    with pytest.raises(ValueError, match="Fan percentage must be between 0 and 100"):
        interface._set_point("fan_percentage", "fast")

@pytest.mark.driver_unit
# Verifies None percentage raises TypeError at the interface reg_type conversion layer.
def test_set_point_fan_percentage_null_raises_type_error():
    interface = Interface()
    register = _DummyRegister(entity_id="fan.office_fan", entity_point="percentage")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"fan": FanHandler()}
    with pytest.raises(TypeError):
        interface._set_point("fan_percentage", None)

@pytest.mark.driver_unit
# Verifies unsupported fan entity point is rejected.
def test_set_point_fan_unsupported_point_raises_error():
    interface = Interface()
    register = _DummyRegister(entity_id="fan.office_fan", entity_point="speed", reg_type=str)
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"fan": FanHandler()}
    with pytest.raises(ValueError, match="Unsupported entity_point for fan: speed"):
        interface._set_point("fan_speed", "high")

# ---------- Light Handler tests ----------

@pytest.mark.driver_unit
# Verifies light writes unsupported point raises an error.
def test_set_point_unsupported_light_point_raises_error():
    interface = Interface()
    register = _DummyRegister(entity_id="light.living_room", entity_point="color", reg_type=str)
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"light": LightHandler()}
    with pytest.raises(ValueError, match="Unsupported light point: color"):
        interface._set_point("light_color", "red")
    

@pytest.mark.driver_unit
# Verifies light writes on follow canary dispatch and generate the expected normalized operation.
def test_set_point_light_success_dispatches_operation():
    interface = Interface()
    register = _DummyRegister(entity_id="light.office_light", entity_point="state")

    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"light": LightHandler()}

    captured = {}

    def _fake_execute_service(operation):
        captured["operation"] = operation

    interface._execute_service = _fake_execute_service

    result = interface._set_point("light_state", 1)

    assert result == 1
    assert register.value == 1
    assert captured["operation"]["service_domain"] == "light"
    assert captured["operation"]["service_name"] == "turn_on"
    assert captured["operation"]["payload"] == {"entity_id": "light.office_light"}

@pytest.mark.driver_unit
# Verifies light writes off follow canary dispatch and generate the expected normalized operation.
def test_set_point_light_state_off_dispatches_operation():
    interface = Interface()
    register = _DummyRegister(entity_id="light.living_room", entity_point="state")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"light": LightHandler()}
    captured = {}
    def _fake_execute_service(operation):
        captured["operation"] = operation
    interface._execute_service = _fake_execute_service
    result = interface._set_point("light_state", 0)
    assert result == 0
    assert register.value == 0
    assert captured["operation"]["service_domain"] == "light"
    assert captured["operation"]["service_name"] == "turn_off"
    assert captured["operation"]["payload"] == {"entity_id": "light.living_room"}


@pytest.mark.driver_unit
# Verifies light writes state out of range raises an error.
def test_set_point_light_state_out_of_range_raises_error():
    interface = Interface()
    register = _DummyRegister(entity_id="light.living_room", entity_point="state")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"light": LightHandler()}
    with pytest.raises(ValueError, match="Light state must be 0 or 1, got: 2"):
        interface._set_point("light_state", 2)

@pytest.mark.driver_unit
# Verifies light writes brightness follow canary dispatch and generate the expected normalized operation.
def test_set_point_light_brightness_dispatches_operation():
    interface = Interface()
    register = _DummyRegister(entity_id="light.living_room", entity_point="brightness")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"light": LightHandler()}
    captured = {}
    def _fake_execute_service(operation):
        captured["operation"] = operation
    interface._execute_service = _fake_execute_service
    result = interface._set_point("light_brightness", 100)
    assert result == 100
    assert register.value == 100
    assert captured["operation"]["service_domain"] == "light"
    assert captured["operation"]["service_name"] == "turn_on"
    assert captured["operation"]["payload"] == {"entity_id": "light.living_room", "brightness": 100}

@pytest.mark.driver_unit
# Verifies light writes brightness at lower bound follows canary dispatch and generate the expected normalized operation.
def test_set_point_light_brightness_at_lower_bound():
    interface = Interface()
    register = _DummyRegister(entity_id="light.living_room", entity_point="brightness")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"light": LightHandler()}
    captured = {}
    def _fake_execute_service(operation):
        captured["operation"] = operation
    interface._execute_service = _fake_execute_service
    result = interface._set_point("light_brightness", 0)
    assert result == 0
    assert register.value == 0
    assert captured["operation"]["service_domain"] == "light"
    assert captured["operation"]["service_name"] == "turn_on"
    assert captured["operation"]["payload"] == {"entity_id": "light.living_room", "brightness": 0}

@pytest.mark.driver_unit
# Verifies light writes brightness at upper bound follows canary dispatch and generate the expected normalized operation.
def test_set_point_light_brightness_at_upper_bound():
    interface = Interface()
    register = _DummyRegister(entity_id="light.living_room", entity_point="brightness")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"light": LightHandler()}
    captured = {}
    def _fake_execute_service(operation):
        captured["operation"] = operation
    interface._execute_service = _fake_execute_service
    result = interface._set_point("light_brightness", 255)
    assert result == 255
    assert register.value == 255
    assert captured["operation"]["service_domain"] == "light"
    assert captured["operation"]["service_name"] == "turn_on"
    assert captured["operation"]["payload"] == {"entity_id": "light.living_room", "brightness": 255}

@pytest.mark.driver_unit
# Verifies light writes brightness above upper bound raises an error.
def test_set_point_light_brightness_above_upper_bound_raises_error():
    interface = Interface()
    register = _DummyRegister(entity_id="light.living_room", entity_point="brightness")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"light": LightHandler()}
    with pytest.raises(ValueError, match="Brightness must be 0-255, got: 256"):
        interface._set_point("light_brightness", 256)

@pytest.mark.driver_unit
# Verifies light writes brightness below lower bound raises an error.
def test_set_point_light_brightness_below_lower_bound_raises_error():
    interface = Interface()
    register = _DummyRegister(entity_id="light.living_room", entity_point="brightness")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"light": LightHandler()}
    with pytest.raises(ValueError, match="Brightness must be 0-255, got: -1"):
        interface._set_point("light_brightness", -1)
    
@pytest.mark.driver_unit
# Verifies light writes brightness non-float raises an error.
def test_set_point_light_brightness_non_float_raises_error():
    interface = Interface()
    register = _DummyRegister(entity_id="light.living_room", entity_point="brightness", reg_type=str)
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"light": LightHandler()}
    with pytest.raises(ValueError, match="Brightness must be 0-255, got: not a number"):
        interface._set_point("light_brightness", "not a number")

# ---------- Climate Handler tests ----------
@pytest.mark.driver_unit
# Verifies climate writes follow canary dispatch and generate the expected normalized operation.
def test_set_point_climate_success_dispatches_operation():
    interface = Interface()
    register = _DummyRegister(entity_id="climate.living_room", entity_point="state")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"climate": ClimateHandler()}
    captured = {}
    def _fake_execute_service(operation):
        captured["operation"] = operation
    interface._execute_service = _fake_execute_service
    result = interface._set_point("climate_state", 2)
    assert result == 2
    assert register.value == 2
    assert captured["operation"]["service_domain"] == "climate"
    assert captured["operation"]["service_name"] == "set_hvac_mode"
    assert captured["operation"]["payload"] == {"entity_id": "climate.living_room", "hvac_mode": "heat"}

@pytest.mark.driver_unit
# Verifies climate writes state out of range raises an error.
def test_set_point_climate_state_out_of_range_raises_error():
    interface = Interface()
    register = _DummyRegister(entity_id="climate.living_room", entity_point="state")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"climate": ClimateHandler()}
    with pytest.raises(ValueError, match="Climate state must be 0, 2, 3, or 4, got: 5"):
        interface._set_point("climate_state", 5)

@pytest.mark.driver_unit
# Verifies climate temperature write dispatches correct operation in Fahrenheit (default).
def test_set_point_climate_temperature_dispatches_operation():
    interface = Interface()
    register = _DummyRegister(entity_id="climate.living_room", entity_point="temperature")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"climate": ClimateHandler()}
    captured = {}
    def _fake_execute_service(operation):
        captured["operation"] = operation
    interface._execute_service = _fake_execute_service
    result = interface._set_point("climate_temperature", 70)
    assert result == 70
    assert register.value == 70
    assert captured["operation"]["service_domain"] == "climate"
    assert captured["operation"]["service_name"] == "set_temperature"
    assert captured["operation"]["payload"] == {"entity_id": "climate.living_room", "temperature": 70}

@pytest.mark.driver_unit
# Verifies Celsius conversion when interface.units is set to "C".
def test_set_point_climate_temperature_celsius_conversion():
    interface = Interface()
    interface.units = "C"
    register = _DummyRegister(entity_id="climate.living_room", entity_point="temperature", reg_type=float)
    interface.get_register_by_name = lambda _: register
    handler = ClimateHandler()
    handler.set_interface(interface)
    interface.handler_registry = {"climate": handler}
    captured = {}
    def _fake_execute_service(operation):
        captured["operation"] = operation
    interface._execute_service = _fake_execute_service
    result = interface._set_point("climate_temperature", 70.0)
    assert result == 70.0
    assert captured["operation"]["service_name"] == "set_temperature"
    assert captured["operation"]["payload"] == {"entity_id": "climate.living_room", "temperature": 21.1}

@pytest.mark.driver_unit
# Verifies temperature at the lower boundary (45) is accepted.
def test_set_point_climate_temperature_at_lower_bound():
    interface = Interface()
    register = _DummyRegister(entity_id="climate.living_room", entity_point="temperature")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"climate": ClimateHandler()}
    captured = {}
    def _fake_execute_service(operation):
        captured["operation"] = operation
    interface._execute_service = _fake_execute_service
    result = interface._set_point("climate_temperature", 45)
    assert result == 45
    assert captured["operation"]["payload"]["temperature"] == 45

@pytest.mark.driver_unit
# Verifies temperature at the upper boundary (95) is accepted.
def test_set_point_climate_temperature_at_upper_bound():
    interface = Interface()
    register = _DummyRegister(entity_id="climate.living_room", entity_point="temperature")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"climate": ClimateHandler()}
    captured = {}
    def _fake_execute_service(operation):
        captured["operation"] = operation
    interface._execute_service = _fake_execute_service
    result = interface._set_point("climate_temperature", 95)
    assert result == 95
    assert captured["operation"]["payload"]["temperature"] == 95

@pytest.mark.driver_unit
# Verifies temperature above 95 is rejected.
def test_set_point_climate_temperature_above_range_raises_error():
    interface = Interface()
    register = _DummyRegister(entity_id="climate.living_room", entity_point="temperature")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"climate": ClimateHandler()}
    with pytest.raises(ValueError, match="Temperature must be between 45"):
        interface._set_point("climate_temperature", 100)

@pytest.mark.driver_unit
# Verifies temperature below 45 is rejected.
def test_set_point_climate_temperature_below_range_raises_error():
    interface = Interface()
    register = _DummyRegister(entity_id="climate.living_room", entity_point="temperature")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"climate": ClimateHandler()}
    with pytest.raises(ValueError, match="Temperature must be between 45"):
        interface._set_point("climate_temperature", 40)

@pytest.mark.driver_unit
# Verifies non-numeric temperature is rejected.
def test_set_point_climate_temperature_non_numeric_raises_error():
    interface = Interface()
    register = _DummyRegister(entity_id="climate.living_room", entity_point="temperature", reg_type=str)
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"climate": ClimateHandler()}
    with pytest.raises(ValueError, match="Temperature must be numeric"):
        interface._set_point("climate_temperature", "hot")

@pytest.mark.driver_unit
# Verifies unsupported climate entity point is rejected.
def test_set_point_climate_unsupported_point_raises_error():
    interface = Interface()
    register = _DummyRegister(entity_id="climate.living_room", entity_point="humidity")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"climate": ClimateHandler()}
    with pytest.raises(ValueError, match="Unsupported climate point: humidity"):
        interface._set_point("climate_humidity", 50)

# ---------- InputBoolean Handler tests ----------

@pytest.mark.driver_unit
# Verifies input_boolean state on dispatches turn_on operation.
def test_set_point_input_boolean_on_dispatches_operation():
    interface = Interface()
    register = _DummyRegister(entity_id="input_boolean.vacation_mode", entity_point="state")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"input_boolean": InputBooleanHandler()}
    captured = {}
    def _fake_execute_service(operation):
        captured["operation"] = operation
    interface._execute_service = _fake_execute_service
    result = interface._set_point("vacation_mode_state", 1)
    assert result == 1
    assert register.value == 1
    assert captured["operation"]["service_domain"] == "input_boolean"
    assert captured["operation"]["service_name"] == "turn_on"
    assert captured["operation"]["payload"] == {"entity_id": "input_boolean.vacation_mode"}

@pytest.mark.driver_unit
# Verifies input_boolean state off dispatches turn_off operation.
def test_set_point_input_boolean_off_dispatches_operation():
    interface = Interface()
    register = _DummyRegister(entity_id="input_boolean.vacation_mode", entity_point="state")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"input_boolean": InputBooleanHandler()}
    captured = {}
    def _fake_execute_service(operation):
        captured["operation"] = operation
    interface._execute_service = _fake_execute_service
    result = interface._set_point("vacation_mode_state", 0)
    assert result == 0
    assert register.value == 0
    assert captured["operation"]["service_domain"] == "input_boolean"
    assert captured["operation"]["service_name"] == "turn_off"
    assert captured["operation"]["payload"] == {"entity_id": "input_boolean.vacation_mode"}

@pytest.mark.driver_unit
# Verifies input_boolean state out of range is rejected.
def test_set_point_input_boolean_state_out_of_range_raises_error():
    interface = Interface()
    register = _DummyRegister(entity_id="input_boolean.vacation_mode", entity_point="state")
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"input_boolean": InputBooleanHandler()}
    with pytest.raises(ValueError, match="InputBoolean value must be 0 or 1, got: 2"):
        interface._set_point("vacation_mode_state", 2)

@pytest.mark.driver_unit
# Verifies input_boolean unsupported entity point is rejected.
def test_set_point_input_boolean_unsupported_point_raises_error():
    interface = Interface()
    register = _DummyRegister(entity_id="input_boolean.vacation_mode", entity_point="brightness", reg_type=str)
    interface.get_register_by_name = lambda _: register
    interface.handler_registry = {"input_boolean": InputBooleanHandler()}
    with pytest.raises(ValueError, match="InputBoolean only supports 'state' point"):
        interface._set_point("vacation_mode_brightness", "high")