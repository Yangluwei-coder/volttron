.. _HomeAssistant-Write-Tutorial:

========================================
Home Assistant Device Write Tutorial
========================================

This tutorial will guide you step-by-step through controlling devices in Home Assistant via VOLTTRON using the **Fan Agent** method.

**Home Assistant Website**: https://www.home-assistant.io

**What you'll learn**: By the end of this tutorial, you will be able to read and control Home Assistant devices (fans, lights, thermostats, and input booleans) through VOLTTRON.

**Estimated time**: 45 minutes

---

Architecture Overview
======================

The full control chain is:

::

    Fan Agent → RPC → platform.driver → home_assistant.py → HA REST API → HA Device

- **Fan Agent**: A VOLTTRON agent that sends RPC calls to platform.driver
- **platform.driver**: VOLTTRON's device driver framework
- **home_assistant.py**: The HA-specific driver interface
- **handlers/**: Per-domain handler classes (fan, light, climate, input_boolean)
- **HA REST API**: Home Assistant's HTTP API (port 8123)

**Supported device domains and points**:

.. list-table::
   :header-rows: 1
   :widths: 20 20 15 45

   * - Domain
     - Entity Point
     - Writable
     - Description
   * - ``fan``
     - ``state``
     - Yes
     - 0 = off, 1 = on
   * - ``fan``
     - ``percentage``
     - Yes
     - Fan speed, 0–100
   * - ``light``
     - ``state``
     - Yes
     - 0 = off, 1 = on
   * - ``light``
     - ``brightness``
     - Yes
     - Brightness level, 0–255
   * - ``climate``
     - ``state``
     - Yes
     - 0=off, 2=heat, 3=cool, 4=auto
   * - ``climate``
     - ``temperature``
     - Yes
     - Target temperature in °F (45–95)
   * - ``input_boolean``
     - ``state``
     - Yes
     - 0 = off, 1 = on (toggles each call)

---

Chapter 1: Install Home Assistant
===================================

1.1 Install Home Assistant via pip
------------------------------------

.. code-block:: bash

    $ pip3 install homeassistant

Start Home Assistant:

.. code-block:: bash

    $ hass

Wait 1-2 minutes for initialization. You will see output like::

    Unable to find configuration. Creating default one in /home/user/.homeassistant

.. note::

    Common warnings during startup (turbojpeg, ffmpeg, aiodns) are non-critical and can be ignored.

1.2 Access Home Assistant
--------------------------

Open your browser and go to:

::

    http://<HA_HOST_IP>:8123

If VOLTTRON and HA are on different machines, replace ``<HA_HOST_IP>`` with the IP address of the machine running HA.

1.3 Create Your Account
-------------------------

When you first open Home Assistant, complete the onboarding:

1. Enter your **name**
2. Create a **username** and **password**
3. Set your **location** and **timezone**
4. Click **Create Account**

---

Chapter 2: Install VOLTTRON
=============================

For detailed VOLTTRON installation instructions, see :ref:`VOLTTRON Quick Start <VOLTTRON-Quick-Start>`.

After installation, bootstrap and start VOLTTRON:

.. code-block:: bash

    $ cd ~/volttron
    $ python3 bootstrap.py
    $ ./start-volttron
    $ source env/bin/activate

---

Chapter 3: Preparation
=======================

3.1 Find Your Home Assistant IP Address
-----------------------------------------

.. code-block:: bash

    # Linux
    $ ip addr show

    # Mac
    $ ipconfig getifaddr en0

Note the IPv4 address (e.g., ``192.168.1.100``). If HA is on the same machine as VOLTTRON, use ``127.0.0.1``.

3.2 Create an Access Token
----------------------------

1. Open the Home Assistant web interface
2. Click your **user avatar** (bottom-left)
3. Select **Profile**
4. Scroll down to **Long-Lived Access Tokens**
5. Click **Create Token**, give it a name (e.g., ``volttron``)
6. Click **Create**
7. **Copy the token immediately** — it will not be shown again

.. warning::

    The token is tied to the specific HA instance. If HA is restarted with a fresh database, you must generate a new token.

3.3 Verify the Connection
--------------------------

.. code-block:: bash

    $ curl -H "Authorization: Bearer YOUR_TOKEN" http://<HA_IP>:8123/api/

You should receive a JSON response. A 401 error means the token is invalid.

---

Chapter 4: Create Test Devices in Home Assistant
==================================================

4.1 Create a Virtual Fan
--------------------------

.. code-block:: bash

    $ nano ~/.homeassistant/configuration.yaml

Add the following:

.. code-block:: yaml

    fan:
      - platform: template
        fans:
          test_fan:
            friendly_name: "Test Fan"
            value_template: "{{ states('input_boolean.test_fan') }}"
            turn_on:
              service: input_boolean.turn_on
              target:
                entity_id: input_boolean.test_fan
            turn_off:
              service: input_boolean.turn_off
              target:
                entity_id: input_boolean.test_fan
            percentage_template: "{{ states('input_number.test_fan_speed') }}"
            set_percentage:
              service: input_number.set_value
              target:
                entity_id: input_number.test_fan_speed
              data:
                value: "{{ percentage }}"

Restart HA after saving. The entity ID will be ``fan.test_fan``.

4.2 Create Other Test Devices
-------------------------------

For lights, thermostats, and input_boolean, use HA's **Helpers** UI:

**Settings → Devices & Services → Helpers → Create Helper**

- Choose **Toggle** to create an ``input_boolean`` entity
- Real lights and thermostats appear automatically once integrated with HA

4.3 Verify Devices Exist
--------------------------

Go to **Developer Tools → States** in HA and search for your entity (e.g., ``fan.test_fan``).

---

Chapter 5: Configure VOLTTRON
==============================

5.1 Create the Config Files
----------------------------

Navigate to your VOLTTRON directory:

.. code-block:: bash

    $ cd ~/volttron

**Create** ``device.config``:

.. code-block:: json

    {
        "driver_config": {
            "ip_address": "YOUR_HA_IP_ADDRESS",
            "access_token": "YOUR_ACCESS_TOKEN",
            "port": "8123"
        },
        "driver_type": "home_assistant",
        "registry_config": "config://test_fan.json",
        "interval": 30,
        "timezone": "UTC"
    }

**Create** ``test_fan.json``:

.. code-block:: json

    [
        {
            "Entity ID": "fan.test_fan",
            "Entity Point": "state",
            "Volttron Point Name": "fan_state",
            "Units": "On / Off",
            "Units Details": "0: off, 1: on",
            "Writable": true,
            "Starting Value": 0,
            "Type": "int",
            "Notes": "Fan on/off state"
        },
        {
            "Entity ID": "fan.test_fan",
            "Entity Point": "percentage",
            "Volttron Point Name": "fan_percentage",
            "Units": "Percent",
            "Units Details": "0 - 100",
            "Writable": true,
            "Starting Value": 0,
            "Type": "int",
            "Notes": "Fan speed percentage"
        }
    ]

5.2 Upload Configs to VOLTTRON
--------------------------------

.. code-block:: bash

    $ vctl config store platform.driver test_fan.json test_fan.json --raw
    $ vctl config store platform.driver devices/test/room/test_fan device.config --json

.. note::

    ``test_fan.json`` must be stored with ``--raw`` and ``device.config`` with ``--json``.

5.3 Install and Start Platform Driver
---------------------------------------

.. code-block:: bash

    $ python scripts/install-agent.py \
        -s services/core/PlatformDriverAgent \
        -c services/core/PlatformDriverAgent/platform-driver.agent \
        -f

    $ vctl status
    # Note the UUID of platform_driveragent-4.0
    $ vctl start <UUID>

Verify the device is being scraped (wait ~30 seconds):

.. code-block:: bash

    $ grep -i "test_fan\|scraping" ~/volttron/volttron.log | tail -10

You should see::

    scraping device: test/room/test_fan
    publishing: devices/test/room/test_fan/all

---

Chapter 6: Control the Fan via Fan Agent
==========================================

.. note::

    Direct ``vctl rpc`` calls to ``platform.driver`` are not supported in this version of VOLTTRON.
    RPC calls must be made from within a VOLTTRON agent.

6.1 Install Actuator Agent
----------------------------

.. code-block:: bash

    $ vctl install services/core/ActuatorAgent --tag actuator
    $ vctl start --tag actuator

6.2 Create Fan Agent Config
-----------------------------

Create ``fan_agent/config.json``:

.. code-block:: json

    {
        "action": 1,
        "action_type": "state"
    }

**Config field explanation**:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Field
     - Description
   * - action
     - The value to set. For ``state``: 0=off, 1=on. For ``percentage``: 0–100.
   * - action_type
     - Either ``state`` (on/off) or ``percentage`` (speed control)

6.3 Install and Start Fan Agent
---------------------------------

.. code-block:: bash

    $ python scripts/install-agent.py \
        -s fan_agent \
        -c fan_agent/config.json \
        -t fan_agent \
        --start \
        -f

    $ vctl status
    # fan_agent-1.0 should show: running [XXXX]  GOOD

The Fan Agent controls the fan ~10 seconds after startup.

6.4 Change Fan Settings
------------------------

.. code-block:: bash

    # Turn fan off
    $ echo '{"action": 0, "action_type": "state"}' > fan_agent/config.json
    $ python scripts/install-agent.py -s fan_agent -c fan_agent/config.json -t fan_agent --start -f

    # Set speed to 50%
    $ echo '{"action": 50, "action_type": "percentage"}' > fan_agent/config.json
    $ python scripts/install-agent.py -s fan_agent -c fan_agent/config.json -t fan_agent --start -f

6.5 Verify the Result
----------------------

Open Home Assistant in your browser and check the state of ``fan.test_fan``.

.. code-block:: bash

    $ grep -i "test_fan\|fan_agent" ~/volttron/volttron.log | tail -20

.. warning::

    The ``TOPIC`` in ``set_point`` RPC calls must **not** include the ``devices/`` prefix.
    Use ``"test/room/test_fan"``, not ``"devices/test/room/test_fan"``.

---

Chapter 7: Other Supported Device Types
==========================================

7.1 Light
----------

**Registry config** (``my_light.json``):

.. code-block:: json

    [
        {
            "Entity ID": "light.my_light",
            "Entity Point": "state",
            "Volttron Point Name": "light_state",
            "Units": "On / Off",
            "Units Details": "0: off, 1: on",
            "Writable": true,
            "Starting Value": 0,
            "Type": "int"
        },
        {
            "Entity ID": "light.my_light",
            "Entity Point": "brightness",
            "Volttron Point Name": "light_brightness",
            "Units": "0-255",
            "Units Details": "0: off, 255: full brightness",
            "Writable": true,
            "Starting Value": 0,
            "Type": "int"
        }
    ]

**Upload and control**:

.. code-block:: bash

    $ vctl config store platform.driver my_light.json my_light.json --raw
    $ vctl config store platform.driver devices/test/room/my_light device.config --json

    # Turn light on
    $ echo '{"action": 1, "action_type": "state"}' > fan_agent/config.json
    $ python scripts/install-agent.py -s fan_agent -c fan_agent/config.json -t fan_agent --start -f

    # Turn light off
    $ echo '{"action": 0, "action_type": "state"}' > fan_agent/config.json
    $ python scripts/install-agent.py -s fan_agent -c fan_agent/config.json -t fan_agent --start -f

    # Set brightness to 128
    $ echo '{"action": 128, "action_type": "brightness"}' > fan_agent/config.json
    $ python scripts/install-agent.py -s fan_agent -c fan_agent/config.json -t fan_agent --start -f

7.2 Thermostat (Climate)
-------------------------

**Registry config** (``my_thermostat.json``):

.. code-block:: json

    [
        {
            "Entity ID": "climate.my_thermostat",
            "Entity Point": "state",
            "Volttron Point Name": "thermostat_state",
            "Units": "Enumeration",
            "Units Details": "0: off, 2: heat, 3: cool, 4: auto",
            "Writable": true,
            "Starting Value": 0,
            "Type": "int"
        },
        {
            "Entity ID": "climate.my_thermostat",
            "Entity Point": "temperature",
            "Volttron Point Name": "set_temperature",
            "Units": "F",
            "Units Details": "45 - 95",
            "Writable": true,
            "Starting Value": 72,
            "Type": "float"
        }
    ]

**Mode mapping**:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - VOLTTRON Value
     - HA HVAC Mode
   * - 0
     - off
   * - 2
     - heat
   * - 3
     - cool
   * - 4
     - auto

**Upload and control**:

.. code-block:: bash

    $ vctl config store platform.driver my_thermostat.json my_thermostat.json --raw
    $ vctl config store platform.driver devices/test/room/my_thermostat device.config --json

    # Set to heat mode
    $ echo '{"action": 2, "action_type": "state"}' > fan_agent/config.json
    $ python scripts/install-agent.py -s fan_agent -c fan_agent/config.json -t fan_agent --start -f

    # Set to cool mode
    $ echo '{"action": 3, "action_type": "state"}' > fan_agent/config.json
    $ python scripts/install-agent.py -s fan_agent -c fan_agent/config.json -t fan_agent --start -f

    # Set temperature to 75°F
    $ echo '{"action": 75, "action_type": "temperature"}' > fan_agent/config.json
    $ python scripts/install-agent.py -s fan_agent -c fan_agent/config.json -t fan_agent --start -f

7.3 Input Boolean
------------------

``input_boolean`` is a simple toggle switch. Each ``set_point`` call toggles its state
regardless of the value passed.

**Registry config** (``my_boolean.json``):

.. code-block:: json

    [
        {
            "Entity ID": "input_boolean.my_switch",
            "Entity Point": "state",
            "Volttron Point Name": "boolean_state",
            "Units": "On / Off",
            "Units Details": "0: off, 1: on",
            "Writable": true,
            "Starting Value": 0,
            "Type": "int"
        }
    ]

**Upload and control**:

.. code-block:: bash

    $ vctl config store platform.driver my_boolean.json my_boolean.json --raw
    $ vctl config store platform.driver devices/test/room/my_boolean device.config --json

    # Toggle the switch
    $ echo '{"action": 1, "action_type": "state"}' > fan_agent/config.json
    $ python scripts/install-agent.py -s fan_agent -c fan_agent/config.json -t fan_agent --start -f

.. note::

    Each call toggles the boolean. Call it twice to return to the original state.

---

Chapter 8: Troubleshooting
============================

8.1 401 Unauthorized
---------------------

Generate a new token in HA (**Profile → Long-Lived Access Tokens → Create Token**), then update:

.. code-block:: bash

    $ sed -i 's/"access_token": ".*"/"access_token": "NEW_TOKEN"/' device.config
    $ vctl config store platform.driver devices/test/room/test_fan device.config --json
    $ vctl restart <platform_driver_UUID>

8.2 Connection Refused
-----------------------

Check HA is running and the IP/port in ``device.config`` are correct:

.. code-block:: bash

    $ ps aux | grep hass
    $ curl http://<HA_IP>:8123/api/

8.3 KeyError on set_point
--------------------------

In the Fan Agent code, change ``TOPIC`` to remove the ``devices/`` prefix:

.. code-block:: python

    TOPIC = "test/room/test_fan"   # correct

8.4 AttributeError: 'str' object has no attribute 'get'
---------------------------------------------------------

In ``home_assistant.py``, add JSON parsing at the start of ``parse_config``:

.. code-block:: python

    def parse_config(self, config_dict):
        if not config_dict:
            return
        if isinstance(config_dict, str):
            config_dict = json.loads(config_dict)

In ``driver.py``, add ``config://`` resolution before the interface is called:

.. code-block:: python

    registry_config = config.get("registry_config")
    if isinstance(registry_config, str) and registry_config.startswith("config://"):
        config_name = registry_config[len("config://"):]
        registry_config = self.vip.config.get(config_name)

Then reinstall the Platform Driver:

.. code-block:: bash

    $ python scripts/install-agent.py \
        -s services/core/PlatformDriverAgent \
        -c services/core/PlatformDriverAgent/platform-driver.agent \
        -f

8.5 Fan Agent Not Starting (status shows ``1``)
------------------------------------------------

Check for import errors and fix:

.. code-block:: bash

    $ grep "fan_agent" ~/volttron/volttron.log | grep ERROR

    $ sed -i 's/from volttron.platform.vip.agent import Agent, Core, rpc_method/from volttron.platform.vip.agent import Agent, Core\nfrom volttron.platform.vip.agent import RPC/' fan_agent/fan_agent/agent.py
    $ sed -i 's/@rpc_method/@RPC.export/' fan_agent/fan_agent/agent.py

    $ python scripts/install-agent.py -s fan_agent -c fan_agent/config.json -t fan_agent --start -f

8.6 Viewing Logs
-----------------

.. code-block:: bash

    $ tail -f ~/volttron/volttron.log
    $ grep -i "test_fan\|home_assistant\|fan_agent" ~/volttron/volttron.log | tail -20
    $ grep "ERROR" ~/volttron/volttron.log | tail -20

---

Chapter 9: Summary
====================

**The complete control chain**:

::

    Fan Agent
        ↓  self.vip.rpc.call("platform.driver", "set_point", ...)
    platform.driver
        ↓  home_assistant.py → handlers/fan.py (or light.py, climate.py, input_boolean.py)
    HA REST API (http://IP:8123/api/services/...)
        ↓
    Home Assistant entity

**Next Steps**:

- Extend the Fan Agent to respond to sensor data automatically
- Use the SQL Historian to log device state over time
- Try controlling multiple devices from a single agent