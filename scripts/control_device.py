#!/usr/bin/env python3
"""
使用 Actuator Agent 控制 Home Assistant 设备的脚本
"""
import sys
from volttron.platform.vip.agent import Agent
from volttron.platform.keystore import KeyStore

def main():
    # 连接到 VOLTTRON
    agent = Agent(address='tcp://127.0.0.1:22916')

    # 启动连接
    agent.core.run()

    device_path = "devices/test/room/test_fan"
    point_name = "fan_state"
    value = 1  # 1 = ON, 0 = OFF

    try:
        # 调用 platform.driver 的 set_point 方法
        result = agent.vip.rpc.call(
            'platform.driver',
            'set_point',
            device_path,
            point_name,
            value
        ).get(timeout=10)
        print(f"成功设置 {point_name} 为 {value}")
        print(f"返回值: {result}")
    except Exception as e:
        print(f"错误: {e}")

    agent.core.stop()

if __name__ == '__main__':
    main()