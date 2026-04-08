#!/usr/bin/env python3
"""
通过 Home Assistant REST API 控制风扇

注意: 此脚本直接调用 HA API，绕过了 VOLTTRON RPC 的 gevent 兼容性问题。
VOLTTRON 的 platform.driver 内部通过 home_assistant.py 调用 HA API，
但外部脚本无法直接调用其 RPC（由于 gevent 事件循环冲突）。

使用方式:
    python scripts/control_ha_device.py ON   # 开启风扇 (100%)
    python scripts/control_ha_device.py OFF  # 关闭风扇
    python scripts/control_ha_device.py 50   # 设置速度 50%
"""
import sys
import os
import requests
import json

# 从 device.config 读取 HA 连接信息（与 platform.driver 使用相同配置）
CONFIG_PATH = os.environ.get('HA_DEVICE_CONFIG',
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'device.config'))

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
    """控制风扇状态"""
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
            # 设置百分比
            data = {"entity_id": "fan.test_fan", "percentage": int(percentage)}
            response = requests.post(f"{base_url}/api/services/fan/set_percentage",
                                   headers=headers, json=data, timeout=5)
        elif state.upper() == "ON":
            # 开启风扇并设置 100% 速度
            data = {"entity_id": "fan.test_fan", "percentage": 100}
            response = requests.post(f"{base_url}/api/services/fan/turn_on",
                                   headers=headers, json=data, timeout=5)
        elif state.upper() == "OFF":
            # 关闭风扇
            data = {"entity_id": "fan.test_fan"}
            response = requests.post(f"{base_url}/api/services/fan/turn_off",
                                   headers=headers, json=data, timeout=5)
        else:
            print(f"无效的状态: {state}")
            return False

        if response.status_code == 200:
            # 解析响应获取风扇状态
            result = response.json()
            for item in result:
                if item.get('entity_id') == 'fan.test_fan':
                    fan_state = item.get('state')
                    fan_percentage = item.get('attributes', {}).get('percentage')
                    print(f"成功! 风扇状态: {fan_state}, 速度: {fan_percentage}%")
                    return True
            print(f"成功!")
            return True
        else:
            print(f"失败! 状态码: {response.status_code}")
            return False

    except Exception as e:
        print(f"错误: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python control_ha_device.py ON   # 开启风扇")
        print("  python control_ha_device.py OFF  # 关闭风扇")
        print("  python control_ha_device.py 50   # 设置速度 50%")
        sys.exit(1)

    arg = sys.argv[1]

    if arg.isdigit():
        percentage = int(arg)
        if 0 <= percentage <= 100:
            success = set_fan_state(None, percentage=percentage)
        else:
            print("百分比必须在 0-100 之间")
            sys.exit(1)
    else:
        success = set_fan_state(arg)

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
