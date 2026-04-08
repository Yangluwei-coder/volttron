#!/usr/bin/env python3
"""
直接通过 platform.driver RPC 控制风扇速度

使用方式:
    python scripts/set_fan_percentage.py 80   # 设置速度为 80%
    python scripts/set_fan_percentage.py 50   # 设置速度为 50%
"""
import sys
import os

os.environ.setdefault('VOLTTRON_HOME', os.path.expanduser('~/.volttron'))

from volttron.platform.control.control_connection import ControlConnection

def set_fan_percentage(speed):
    """通过 platform.driver 设置风扇百分比"""
    print(f"正在设置风扇速度为 {speed}%...")

    device_path = "test/room/test_fan"
    point_name = "fan_percentage"

    try:
        conn = ControlConnection('tcp://127.0.0.1:22916')
        result = conn.call('platform.driver', 'set_point', device_path, point_name, speed)
        print(f"成功! 返回值: {result}")
        return True
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    if len(sys.argv) < 2:
        print("用法: python set_fan_percentage.py <速度百分比>")
        print("示例: python set_fan_percentage.py 80")
        sys.exit(1)

    try:
        speed = int(sys.argv[1])
        if not 0 <= speed <= 100:
            print("错误: 速度必须在 0-100 之间")
            sys.exit(1)
    except ValueError:
        print("错误: 请输入有效的数字")
        sys.exit(1)

    success = set_fan_percentage(speed)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
