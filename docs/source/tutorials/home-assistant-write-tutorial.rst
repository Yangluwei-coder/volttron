.. _HomeAssistant-Write-Tutorial:

========================================
Home Assistant Fan Control with VOLTTRON
========================================

This guide helps customer teams control fan state and speed through VOLTTRON and verify that commands are applied correctly in Home Assistant.

**Home Assistant Website**: https://www.home-assistant.io

For full driver capabilities, supported writable points, and registry examples across domains,
see :ref:`Home Assistant Driver <HomeAssistant-Driver>`.

**What you will achieve:**

- Turn a fan on and off from VOLTTRON
- Set fan speed percentage
- Confirm expected behavior in the Home Assistant UI and logs

---

Architecture Overview
======================

The full control chain is:

.. mermaid::

   flowchart TD
      A[Agent or CLI<br/>RPC set_point / get_point] --> B[platform.driver]
      B --> C[home_assistant interface<br/>home_assistant.py]
      C --> D[handlers/<br/>FanHandler, LightHandler,<br/>ClimateHandler, InputBooleanHandler]
      D --> E[HA REST API<br/>http://&lt;HA_IP&gt;:8123/api/services/...]
      E --> F[Home Assistant entity]

- **platform.driver**: VOLTTRON's device driver framework
- **home_assistant.py**: The HA-specific driver interface
- **handlers/**: Per-domain handler classes (``FanHandler``, ``LightHandler``, ``ClimateHandler``, ``InputBooleanHandler``)
- **HA REST API**: Home Assistant's HTTP API (port 8123)

---

Chapter 1: Home Assistant Prerequisites
=========================================

1.1 Create Helper Entities
---------------------------

In the HA web UI: **Settings → Devices & Services → Helpers → Create Helper**

- **Toggle** — Name: ``fan_state`` → creates ``input_boolean.fan_state``
- **Number** — Name: ``fan_speed``, Min: 0, Max: 100 → creates ``input_number.fan_speed``

1.2 Add Template Fan to configuration.yaml
-------------------------------------------

.. code-block:: bash

    $ docker exec -it homeassistant bash
    $ vi /config/configuration.yaml

Add the following at the end of the file:

.. code-block:: yaml

    fan:
      - platform: template
        fans:
          volttron_test_fan:
            friendly_name: "Volttron Test Fan"
            value_template: "{{ states('input_boolean.fan_state') }}"
            percentage_template: "{{ states('input_number.fan_speed') }}"
            turn_on:
              service: input_boolean.turn_on
              target:
                entity_id: input_boolean.fan_state
            turn_off:
              service: input_boolean.turn_off
              target:
                entity_id: input_boolean.fan_state
            set_percentage:
              service: input_number.set_value
              target:
                entity_id: input_number.fan_speed
              data:
                value: "{{ percentage }}"

1.3 Restart Home Assistant
---------------------------

.. code-block:: bash

    $ exit   # exit the container shell first
    $ docker restart homeassistant

Verify that ``fan.volttron_test_fan`` appears in the HA dashboard.

1.4 Generate a Long-Lived Access Token
----------------------------------------

In the HA web UI: click your **username** (bottom left) → scroll to **Long-Lived Access Tokens** → **Create Token** → copy the token.

.. warning::

    Copy the token immediately — it will not be shown again.

---

Chapter 2: How to Validate It Works
====================================

Use one of the following validation paths based on your operational workflow.

Recommended Validation Workflow
-------------------------------

Use this checklist to validate the integration from an operations perspective:

- Run control actions from the **CLI** (the HA web UI is used to visually verify state changes).
- Show one **existing** functionality still works (recommended: ``input_boolean`` state write/read).
- Show the **new** functionality works (``fan`` state and ``fan`` percentage write/read).
- Generate local docs (for example, ``make html`` under ``docs/``) and open the built HTML in a browser.
- Briefly walk through this tutorial and the :ref:`Home Assistant Driver <HomeAssistant-Driver>` page
  to show how teams can repeat the workflow.

2.1 UI Validation (Primary)
----------------------------

For most deployments, use CLI actions with UI verification:

- Trigger state updates from the CLI or an agent workflow.
- Verify ``input_boolean`` state changes in the Home Assistant UI.
- Verify ``fan.volttron_test_fan`` on/off and percentage changes in the Home Assistant UI.
- Review logs to confirm the write path completes without errors.

This path is sufficient for functional validation. The automated tests below are optional additional evidence.

**Existing capability check (input_boolean):**

1. Trigger an ``input_boolean`` state change from the CLI or your agent workflow.
2. In the Home Assistant UI, confirm the corresponding ``input_boolean`` entity changes state.
3. In logs, confirm the write path completed without blocking errors.

Expected result: the ``input_boolean`` state reflects the requested command and remains readable through the driver.

**Acceptance criteria:**

- Existing toggle behavior (``input_boolean``) changes to the requested state.
- Fan on/off state matches the requested command.
- Fan percentage matches the requested value.
- ``input_boolean`` state change is visible in the Home Assistant UI and confirmed in logs.
- Relevant driver/log entries show successful execution and no blocking errors.

2.2 Advanced: Automated Test Validation (Optional)
---------------------------------------------------

Use this section when your team needs automated regression evidence in addition to UI and log verification.

Test Files
-----------

**test_ha_fan_live.py (Standalone — Recommended)**

Location: ``services/core/PlatformDriverAgent/tests/test_ha_fan_live.py``

Tests the fan write path end-to-end against a live HA instance **without requiring a running VOLTTRON platform**.
It calls the HA REST API directly using ``requests``.

- Each test is guarded by ``skip_if_no_env`` and will be skipped if the required environment variables are not set.
- A ``reset_fan`` fixture with yield-based teardown runs after every test to restore the fan and speed helper to their initial state (off / 0), preventing test pollution.

**Test coverage:**

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Test
     - What it verifies
   * - ``test_fan_get_point``
     - Reading fan state returns ``"off"`` when fan is off
   * - ``test_fan_set_point_on``
     - Calling turn_on sets state to ``"on"``
   * - ``test_fan_set_point_off``
     - Calling turn_off sets state to ``"off"``
   * - ``test_fan_set_point_percentage``
     - Setting percentage to 60 reflects in ``input_number.fan_speed``
   * - ``test_fan_scrape_all``
     - Both ``fan.volttron_test_fan`` and ``input_number.fan_speed`` are readable

**test_home_assistant.py (VOLTTRON Platform Integration)**

Location: ``services/core/PlatformDriverAgent/tests/test_home_assistant.py``

Runs through the full VOLTTRON platform driver stack, including ``_set_point → handler_registry →
FanHandler.build_operation → _execute_service``. This suite requires a running VOLTTRON instance and uses the
``volttron_instance`` fixture from ``volttrontesting``.

Fan-specific additions include a ``fan_config_store`` fixture that registers ``fan.volttron_test_fan``
with both ``state`` and ``percentage`` points, and a yield-based teardown that resets the fan helpers after each test.

2.3 Step 1: Set Environment Variables
---------------------------------------

.. code-block:: bash

    $ export HOMEASSISTANT_TEST_IP="localhost"
    $ export ACCESS_TOKEN="your_long_lived_token_here"
    $ export PORT="8123"

2.4 Step 2: Activate the VOLTTRON Virtual Environment
------------------------------------------------------

.. code-block:: bash

    $ source /path/to/volttron/env/bin/activate

2.5 Step 3: Run the Standalone Live Tests
------------------------------------------

.. code-block:: bash

    $ python -m pytest services/core/PlatformDriverAgent/tests/test_ha_fan_live.py -v

Expected output::

    test_ha_fan_live.py::test_fan_get_point PASSED
    test_ha_fan_live.py::test_fan_set_point_on PASSED
    test_ha_fan_live.py::test_fan_set_point_off PASSED
    test_ha_fan_live.py::test_fan_set_point_percentage PASSED
    test_ha_fan_live.py::test_fan_scrape_all PASSED

    5 passed in 6.36s

2.6 Step 4: Run the Unit Dispatch Tests (no HA required)
---------------------------------------------------------

.. code-block:: bash

    $ python -m pytest \
        services/core/PlatformDriverAgent/tests/test_home_assistant_handler_dispatch.py \
        -v -m driver_unit

These tests mock the HA API and validate that the handler registry correctly dispatches fan write
operations without any network calls.

2.7 Environment Constraints
----------------------------

.. note::

    - Tests in ``test_home_assistant.py`` that depend on ``volttron_instance`` require a fully configured
      VOLTTRON environment and will show ``ERROR`` if VOLTTRON is not running locally.
    - Tests tagged with ``RabbitMQ is not setup`` are automatically skipped in environments without
      RabbitMQ/SSL configured — this is expected behavior.
    - The standalone ``test_ha_fan_live.py`` has no VOLTTRON dependency and is the recommended way
      to validate the fan write path in a local development environment.
    - All tests default to **skipped** unless the three environment variables
      (``HOMEASSISTANT_TEST_IP``, ``ACCESS_TOKEN``, ``PORT``) are set in the same shell session before running pytest.
---

Reference Table
===============

All supported domains, entity points, writability, and value semantics:

.. list-table::
   :header-rows: 1
   :widths: 20 20 15 45

   * - Domain
     - Entity Point
     - Writable
     - Value Semantics
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
     - 0 = off, 2 = heat, 3 = cool, 4 = auto
   * - ``climate``
     - ``temperature``
     - Yes
     - Target temperature in °F (45–95)
   * - ``input_boolean``
     - ``state``
     - Yes
     - 0 = off, 1 = on (toggles each call)
