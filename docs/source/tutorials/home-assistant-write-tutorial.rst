.. _HomeAssistant-Write-Tutorial:

========================================
Home Assistant Device Write Tutorial
========================================

This tutorial will guide you step-by-step through controlling devices in Home Assistant via VOLTTRON (specifically, the **Write/Control** functionality).

**Home Assistant Website**: https://www.home-assistant.io

**What you'll learn**: By the end of this tutorial, you will be able to turn a Home Assistant fan on/off and adjust its speed through VOLTTRON.

**Estimated time**: 45 minutes

---

Chapter 1: Install Home Assistant
===================================

Before you begin, you need to install Home Assistant. This chapter shows how to install Home Assistant using Docker.

1.1 Install Docker
-------------------

First, install Docker on your machine.

**For Ubuntu/Debian**:

.. code-block:: bash

    $ sudo apt-get update
    $ sudo apt-get install docker.io docker-compose

**For Mac/Windows**:

Download Docker Desktop from https://www.docker.com/products/docker-desktop

Start Docker:

.. code-block:: bash

    $ sudo systemctl start docker
    $ sudo systemctl enable docker

Verify Docker installation:

.. code-block:: bash

    $ docker --version
    # expected output: Docker version 20.x.x or higher

1.2 Create Home Assistant Container
-------------------------------------

Create a folder for Home Assistant data:

.. code-block:: bash

    $ mkdir -p ~/homeassistant/config

Create the Docker container:

.. code-block:: bash

    $ docker run -d \
      --name homeassistant \
      --restart unless-stopped \
      -p 8123:8123 \
      -v ~/homeassistant/config:/config \
      --network host \
      ghcr.io/home-assistant/home-assistant:stable

**Explanation of parameters**:

- ``-d``: Run in background (detached mode)
- ``--name homeassistant``: Container name
- ``-p 8123:8123``: Map port 8123 (Home Assistant default port)
- ``-v ~/homeassistant/config:/config``: Map local folder to container config
- ``--network host``: Use host network (easier for local access)

1.3 Access Home Assistant
--------------------------

Wait about 5 minutes for Home Assistant to start, then open your browser:

**http://localhost:8123** (if on the same machine)

or

**http://YOUR_IP:8123** (if accessing from another machine)

Replace ``YOUR_IP`` with your machine's IP address.

1.4 Create Your Account
-------------------------

When you first open Home Assistant, you'll see the setup screen:

1. Enter your **name**
2. Create a **username** and **password**
3. Set your **location** (for weather/time)
4. Select your **timezone**
5. Choose your **language**

Click **Create Account** when ready.

**Important**: After creating your account, you'll also need to create a Long-Lived Access Token for VOLTTRON. This will be covered in Chapter 3.

---

Chapter 2: Install VOLTTRON
=============================

For detailed VOLTTRON installation instructions, see :ref:`VOLTTRON Quick Start <VOLTTRON-Quick-Start>`.

---

Chapter 3: Preparation
=======================

3.1 Find Your Home Assistant IP Address
-----------------------------------------

**Steps**:

1. Open the Home Assistant web interface
2. Click your user icon in the top-right corner
3. Select **System**
4. Click **Network**
5. Find the **IPv4** address, for example ``192.168.1.100``

**Remember this address** - you will need it later.

3.2 Create an Access Token
----------------------------

VOLTTRON needs a "key" to access your Home Assistant. This key is called a **Long-Lived Access Token**.

**Steps**:

1. In the Home Assistant interface, click your user icon in the top-right
2. Select **Profile**
3. Scroll down to find **Long-Lived Access Tokens**
4. Click **Create Token**

5. Give the token a name, such as ``volttron``
6. Click **Create**

7. **Important**: Immediately copy the displayed token string! You won't be able to see it after closing.

**A token looks something like this**:

::

    eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI...

Save it somewhere safe.

---

Chapter 4: Create a Test Device
================================

4.1 Create a Virtual Device in Home Assistant
-----------------------------------------------

For testing purposes, let's create a virtual fan in Home Assistant.

**Steps**:

1. Open Home Assistant (https://www.home-assistant.io)
2. Click **Settings** in the left menu
3. Select **Devices & Services**
4. Click **Helpers**
5. Click **Create Helper** (bottom-right)

6. Choose the **Fan** type

7. Enter the name ``test_fan``, then click **Create**

**Your virtual fan is ready!** It should appear in HA's entity list as ``fan.test_fan``.

4.2 Verify the Device Exists
-----------------------------

1. In Home Assistant, press ``Ctrl + E`` on your keyboard (or click the search icon)
2. Type ``test_fan``
3. You should see the fan you just created

---

Chapter 5: Configure VOLTTRON
==============================

Now we need to tell VOLTTRON how to connect to Home Assistant and which device to control.

**You need to create two configuration files**:

1. **Device Connection Config** - tells VOLTTRON how to connect to HA
2. **Device Point Config** - tells VOLTTRON what to control

5.1 Create the Config Files
----------------------------

Create a folder somewhere convenient (e.g., on your desktop), called ``volttron_configs``.

**Step 1: Create the Device Connection Config**

Inside the folder, create a file named ``device.config``:

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

**Important**: Replace ``YOUR_HA_IP_ADDRESS`` with your actual HA IP address and ``YOUR_ACCESS_TOKEN`` with the token you copied.

**Step 2: Create the Device Point Config**

In the same folder, create ``test_fan.json``:

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
            "Notes": "Test fan"
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

**Configuration Field Explanation**:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Field
     - Description
   * - Entity ID
     - The full device ID in HA (note: includes the ``fan.`` prefix)
   * - Entity Point
     - The specific attribute to control (``state`` = fan state, ``percentage`` = speed)
   * - Volttron Point Name
     - A name you give this control point
   * - Writable
     - ``true`` means it can be controlled through VOLTTRON
   * - Type
     - Data type (``int`` = integer)

5.2 Upload Configs to VOLTTRON
------------------------------

Open your terminal and navigate to the folder containing the config files, then run these commands:

**Step 1: Upload the Device Point Config**

.. code-block:: bash

    $ vctl config store platform.driver test_fan.json test_fan.json

**Step 2: Upload the Device Connection Config**

.. code-block:: bash

    $ vctl config store platform.driver devices/test/room/test_fan device.config

**Step 3: Restart the Driver**

.. code-block:: bash

    $ vctl restart platform.driver

**Verify Success**

Check the status:

.. code-block:: bash

    $ vctl status

You should see something like:

::

    listeneragent-3.3  ...  running [1234]  GOOD
    platform.driver           ...  running [5678]  GOOD

---

Chapter 6: Control the Device
==============================

VOLTTRON provides three methods to control Home Assistant devices. Choose the one that fits your needs.

6.1 Method 1: Using Control Scripts (Recommended)
-------------------------------------------------

We've created convenient control scripts to set fan state and speed directly.

**Important Note on Architecture**:

VOLTTRON's ``platform.driver`` internally uses ``home_assistant.py`` to call the Home Assistant REST API. However, external scripts cannot directly call VOLTTRON RPC due to gevent event loop conflicts.

This script calls the HA REST API directly, which is the same API that VOLTTRON uses internally.

**First, create the control script** ``scripts/control_ha_device.py``:

.. code-block:: python

    #!/usr/bin/env python3
    """
    Script to control Home Assistant devices via HA REST API

    Usage:
        python scripts/control_ha_device.py ON   # Turn fan on (100%)
        python scripts/control_ha_device.py OFF  # Turn fan off
        python scripts/control_ha_device.py 50   # Set speed to 50%
    """
    import sys
    import os
    import requests
    import json

    # 从 device.config 读取 HA 连接信息（与 platform.driver 使用相同配置）
    CONFIG_PATH = os.environ.get('HA_DEVICE_CONFIG', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'device.config'))

    def load_config():
        """加载 HA 连接配置"""
        try:
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
            return config.get('driver_config', {})
        except Exception as e:
            print(f"读取配置文件失败: {e}")
            return None

    def set_fan_state(state, percentage=None):
        """Control fan state"""
        config = load_config()
        if not config:
            return False

        ip_address = config.get('ip_address', '127.0.0.1')
        access_token = config.get('access_token', '')
        port = config.get('port', '8123')

        base_url = f"http://{ip_address}:{port}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        try:
            if percentage is not None:
                data = {"entity_id": "fan.test_fan", "percentage": int(percentage)}
                response = requests.post(f"{base_url}/api/services/fan/set_percentage", headers=headers, json=data)
            elif state.upper() == "ON":
                data = {"entity_id": "fan.test_fan", "percentage": 100}
                response = requests.post(f"{base_url}/api/services/fan/turn_on", headers=headers, json=data)
            elif state.upper() == "OFF":
                data = {"entity_id": "fan.test_fan"}
                response = requests.post(f"{base_url}/api/services/fan/turn_off", headers=headers, json=data)
            else:
                return False

            if response.status_code == 200:
                print(f"Success!")
                return True
            return False
        except Exception as e:
            print(f"Error: {e}")
            return False

    def main():
        if len(sys.argv) < 2:
            print("Usage: control_ha_device.py <ON|OFF|0-100>")
            sys.exit(1)

        arg = sys.argv[1]
        if arg.isdigit():
            success = set_fan_state(None, percentage=int(arg))
        else:
            success = set_fan_state(arg)

        sys.exit(0 if success else 1)

    if __name__ == '__main__':
        main()

**Turn ON the fan**:

.. code-block:: bash

    $ cd volttron
    $ source env/bin/activate
    $ python scripts/control_ha_device.py ON

**Turn OFF the fan**:

.. code-block:: bash

    $ python scripts/control_ha_device.py OFF

**Set fan speed percentage** (0-100):

.. code-block:: bash

    $ python scripts/control_ha_device.py 50   # Set to 50%

**Note**: Method 1 directly calls the Home Assistant REST API, bypassing VOLTTRON RPC to avoid gevent compatibility issues.

6.2 Method 2: Using Fan Agent
--------------------------------

The Fan Agent is an automation agent that automatically sets fan state and speed on startup by calling platform.driver RPC.

**Step 1: Install Fan Agent**

Ensure Actuator Agent is installed and running:

.. code-block:: bash

    $ vctl install services/core/ActuatorAgent --tag actuator
    $ vctl start --tag actuator

**Important: The Fan Agent's device path must include the "devices/" prefix!**

In the agent code, the device path is defined as:

.. code-block:: python

    TOPIC = "devices/test/room/test_fan"  # Note: must include "devices/" prefix!

If you see errors like ``KeyError: 'test/room/test_fan'``, check that the path includes the "devices/" prefix.

**Step 2: Create Fan Agent Config**

Create config file ``fan_agent/config.json``:

.. code-block:: json

    {
        "action": 1,
        "action_type": "state"
    }

Or set percentage speed:

.. code-block:: json

    {
        "action": 80,
        "action_type": "percentage"
    }

**Config Explanation**:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Field
     - Description
   * - action
     - Action value (state mode: 0=off, 1=on; percentage mode: 0-100)
   * - action_type
     - Action type (``state`` or ``percentage``)

**Step 3: Install and Start Fan Agent**

The Fan Agent uses platform.driver RPC to control devices, which requires the device path to include the "devices/" prefix.

.. code-block:: bash

    $ cd fan_agent
    $ python setup.py bdist_wheel

    # If vctl install fails with permission errors, try:
    $ cd ..
    $ source env/bin/activate
    $ vctl install fan_agent/dist/fan_agent-1.0-py3-none-any.whl --tag fan_agent

    # Or use the install script:
    $ python scripts/install-agent.py -s fan_agent -t fan_agent --start

    $ vctl start --tag fan_agent

The Fan Agent will automatically set the fan to the configured state on startup.

**Step 4: Change Fan Settings**

To change fan settings, simply modify the config file and restart the Agent:

.. code-block:: bash

    # Edit config
    $ vctl config edit fan_agent config.json
    # Restart Agent
    $ vctl restart --tag fan_agent

6.3 Method 3: Direct RPC Calls (Requires Special Setup)
---------------------------------------------------

Direct RPC calls to platform.driver have gevent compatibility issues in external scripts. However, RPC **does work** when called from within a VOLTTRON agent.

**Why RPC doesn't work in external scripts**: The ControlConnection and Agent classes use gevent for async operations. When run outside the VOLTTRON environment, gevent conflicts with the standard event loop, causing hangs on RPC calls.

**If you need RPC, use one of these approaches**:

1. **Call from within an agent** (e.g., the Fan Agent in Method 2)
2. **Modify the Fan Agent's config and restart** to trigger RPC calls
3. **Use the HA REST API directly** (Method 1)

For this tutorial, Method 1 is recommended as it's the most straightforward and reliable.

**Verify the Result**

Go back to the Home Assistant web interface and find ``test_fan``. You should see its state has changed!

---

Chapter 7: Other Supported Device Types
=========================================

In addition to the fan demonstrated above, the Home Assistant Driver supports the following device types:

7.1 Lights
-----------

Can control state and brightness.

**Config Example**:

.. code-block:: json

    [
        {
            "Entity ID": "light.living_room",
            "Entity Point": "state",
            "Volttron Point Name": "light_state",
            "Units": "On / Off",
            "Units Details": "0: off, 1: on",
            "Writable": true,
            "Starting Value": 0,
            "Type": "int"
        },
        {
            "Entity ID": "light.living_room",
            "Entity Point": "brightness",
            "Volttron Point Name": "light_brightness",
            "Units": "Percent",
            "Units Details": "0 - 255",
            "Writable": true,
            "Starting Value": 0,
            "Type": "int"
        }
    ]

**State Mapping**:

.. list-table::
   :header-rows: 1

   * - HA State
     - VOLTTRON Value
   * - off
     - 0
   * - on
     - 1

**Brightness**: HA uses 0-255 range, VOLTTRON uses the same range directly.

7.2 Thermostats (Climate)
-------------------------

Can control mode and target temperature.

**Config Example**:

.. code-block:: json

    [
        {
            "Entity ID": "climate.my_thermostat",
            "Entity Point": "state",
            "Volttron Point Name": "thermostat_state",
            "Units": "Enumeration",
            "Units Details": "0: Off, 2: heat, 3: Cool, 4: Auto",
            "Writable": true,
            "Starting Value": 0,
            "Type": "int"
        },
        {
            "Entity ID": "climate.my_thermostat",
            "Entity Point": "temperature",
            "Volttron Point Name": "set_temperature",
            "Units": "F",
            "Writable": true,
            "Starting Value": 72,
            "Type": "float"
        }
    ]

**Mode Mapping**:

.. list-table::
   :header-rows: 1

   * - HA Mode
     - VOLTTRON Value
   * - off
     - 0
   * - heat
     - 2
   * - cool
     - 3
   * - auto
     - 4

7.3 Fans (with Percentage Control)
---------

Can control state and speed percentage.

**Config Example**:

.. code-block:: json

    [
        {
            "Entity ID": "fan.living_room",
            "Entity Point": "state",
            "Volttron Point Name": "fan_state",
            "Units": "On / Off",
            "Units Details": "0: off, 1: on",
            "Writable": true,
            "Starting Value": 0,
            "Type": "int"
        },
        {
            "Entity ID": "fan.living_room",
            "Entity Point": "percentage",
            "Volttron Point Name": "fan_percentage",
            "Units": "Percent",
            "Units Details": "Fan speed percentage, 0 - 100",
            "Writable": true,
            "Starting Value": 0,
            "Type": "int"
        }
    ]

---

Chapter 8: Troubleshooting
==========================

8.1 Connection Failed
----------------------

**Problem**: VOLTTRON cannot connect to Home Assistant

**Solutions**:

1. Check if the IP address is correct
2. Check if the port is 8123 (default)
3. Check if the token is correct (try generating a new one)
4. Make sure both are on the same network

8.2 Device Not Found
--------------------

**Problem**: Error message "Entity not found"

**Solutions**:

1. Verify the device ID in Home Assistant
2. Check if Entity ID includes the correct prefix (e.g., ``light.``, ``climate.``)
3. Use HA's developer tools to check the entity list

**How to view entity list**:

1. In Home Assistant, press ``Ctrl + Shift + D`` to open developer tools
2. Click **States**
3. Search for your device

8.3 Command Has No Effect
---------------------------

**Problem**: Device doesn't respond after sending command

**Solutions**:

1. Check if ``Writable`` field is set to ``true``
2. Check if the data format is correct
3. Check if HA device state is "available" (not "unavailable")
4. Check logs for more information

8.4 Viewing Logs
-----------------

View VOLTTRON logs:

.. code-block:: bash

    $ tail -f volttron.log

View only Home Assistant related logs:

.. code-block:: bash

    $ grep -i "home" volttron.log

---

Chapter 9: Summary
==================

Congratulations on completing the Home Assistant Write Tutorial!

**What you've learned**:

- How to install Home Assistant using Docker
- How to install VOLTTRON
- How to get Home Assistant connection information
- How to create VOLTTRON configuration files
- How to control HA devices through VOLTTRON
- Supported device types

**Next Steps**:

- Try controlling a real device (like a real fan)
- Try more complex devices (like thermostats)
- Learn how to control multiple devices at once

---

Appendix: Complete Config Templates
===================================

A.1 Fan Config
----------------

**device.config**:

.. code-block:: json

    {
        "driver_config": {
            "ip_address": "YOUR_HA_IP",
            "access_token": "YOUR_TOKEN",
            "port": "8123"
        },
        "driver_type": "home_assistant",
        "registry_config": "config://my_fan.json",
        "interval": 30
    }

**my_fan.json**:

.. code-block:: json

    [
        {
            "Entity ID": "fan.my_fan",
            "Entity Point": "state",
            "Volttron Point Name": "fan_state",
            "Units": "On / Off",
            "Writable": true,
            "Starting Value": 0,
            "Type": "int"
        },
        {
            "Entity ID": "fan.my_fan",
            "Entity Point": "percentage",
            "Volttron Point Name": "fan_percentage",
            "Units": "Percent",
            "Units Details": "0 - 100",
            "Writable": true,
            "Starting Value": 0,
            "Type": "int"
        }
    ]

A.2 Light Config
---------------------

**device.config**:

.. code-block:: json

    {
        "driver_config": {
            "ip_address": "YOUR_HA_IP",
            "access_token": "YOUR_TOKEN",
            "port": "8123"
        },
        "driver_type": "home_assistant",
        "registry_config": "config://my_light.json",
        "interval": 30
    }

**my_light.json**:

.. code-block:: json

    [
        {
            "Entity ID": "light.my_light",
            "Entity Point": "state",
            "Volttron Point Name": "light_state",
            "Units": "On / Off",
            "Writable": true,
            "Starting Value": 0,
            "Type": "int"
        }
    ]

A.3 Thermostat Config
---------------------

**device.config**:

.. code-block:: json

    {
        "driver_config": {
            "ip_address": "YOUR_HA_IP",
            "access_token": "YOUR_TOKEN",
            "port": "8123"
        },
        "driver_type": "home_assistant",
        "registry_config": "config://thermostat.json",
        "interval": 30
    }

**thermostat.json**:

.. code-block:: json

    [
        {
            "Entity ID": "climate.my_thermostat",
            "Entity Point": "state",
            "Volttron Point Name": "mode",
            "Units": "Enumeration",
            "Units Details": "0: Off, 2: heat, 3: Cool, 4: Auto",
            "Writable": true,
            "Starting Value": 0,
            "Type": "int"
        },
        {
            "Entity ID": "climate.my_thermostat",
            "Entity Point": "temperature",
            "Volttron Point Name": "set_temp",
            "Units": "F",
            "Writable": true,
            "Starting Value": 72,
            "Type": "float"
        }
    ]
