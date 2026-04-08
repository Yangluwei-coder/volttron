"""
Minimal agent to set fan state via RPC to platform.driver.
Install: ./env/bin/python scripts/install-agent.py fan_control/ agent.yaml fan_control
Run: vctl start --tag fan_control
"""
import sys
import logging
from volttron.platform.vip.agent import Agent, Core
from volttron.platform.agent import utils

utils.setup_logging()
_log = logging.getLogger(__name__)

def main():
    agent = FanControlAgent()
    try:
        agent.core.main()
    except KeyboardInterrupt:
        pass

class FanControlAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @Core.receiver("onstart")
    def onstart(self, sender, **kwargs):
        topic = sys.argv[2] if len(sys.argv) > 2 else "devices/test/room/test_fan"
        point = sys.argv[3] if len(sys.argv) > 3 else "fan_state"
        value = int(sys.argv[4]) if len(sys.argv) > 4 else 0

        _log.info(f"Setting {topic}/{point} = {value}")
        try:
            result = self.vip.rpc.call(
                "platform.driver",
                "set_point",
                topic,
                point,
                value
            ).get(timeout=10)
            _log.info(f"Result: {result}")
        except Exception as e:
            _log.error(f"Error: {e}")

if __name__ == "__main__":
    main()
