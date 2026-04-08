import sys
import gevent
from volttron.platform.vip.agent import Agent, Core, rpc_method
from volttron.platform.agent import utils
from volttron.platform.scheduling import periodic
import logging

_log = logging.getLogger(__name__)
__version__ = "1.0"

TOPIC = "devices/test/room/test_fan"
STATE_POINT = "fan_state"
PERCENTAGE_POINT = "fan_percentage"

class FanControlAgent(Agent):

    def __init__(self, config_path, **kwargs):
        super().__init__(**kwargs)
        config = utils.load_config(config_path)
        self.action = config.get("action", 1)
        self.action_type = config.get("action_type", "state")

    @Core.receiver("onstart")
    def on_start(self, sender, **kwargs):
        _log.info(f"FanControlAgent 启动，topic={TOPIC} action={self.action} type={self.action_type}")
        gevent.sleep(10)
        try:
            if self.action_type == "state":
                point_name = STATE_POINT
            else:
                point_name = PERCENTAGE_POINT

            result = self.vip.rpc.call(
                "platform.driver",
                "set_point",
                TOPIC,
                point_name,
                self.action
            ).get(timeout=30)
            _log.info(f"风扇控制成功，类型={self.action_type}，值={self.action}，结果: {result}")
        except Exception as e:
            _log.error(f"RPC 调用失败: {e}")
        self.core.schedule(periodic(60), self.keep_alive)

    def keep_alive(self):
        _log.debug("FanControlAgent 运行中...")

    @rpc_method
    def set_fan_speed(self, speed):
        """
        通过 RPC 设置风扇速度
        speed: 百分比值 0-100
        """
        _log.info(f"RPC 调用: 设置风扇速度为 {speed}%")
        try:
            result = self.vip.rpc.call(
                "platform.driver",
                "set_point",
                TOPIC,
                PERCENTAGE_POINT,
                speed
            ).get(timeout=30)
            _log.info(f"设置成功: {result}")
            return {"success": True, "value": result}
        except Exception as e:
            _log.error(f"设置失败: {e}")
            return {"success": False, "error": str(e)}

def main():
    utils.vip_main(FanControlAgent, version=__version__)

if __name__ == "__main__":
    main()
