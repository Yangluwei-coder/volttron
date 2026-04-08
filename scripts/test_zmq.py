#!/usr/bin/env python3
"""简单的测试脚本"""
import os
os.environ.setdefault('VOLTTRON_HOME', os.path.expanduser('~/.volttron'))

print("测试 ZMQ 连接...")
import zmq

ctx = zmq.Context()
s = ctx.socket(zmq.REQ)
try:
    s.settimeout(5)  # 新版本用 .timeout
except:
    pass
try:
    print("正在连接 tcp://127.0.0.1:22916...")
    s.connect('tcp://127.0.0.1:22916')
    print("已连接，发送 hello...")
    s.send(b'hello')
    print("等待响应...")
    msg = s.recv()
    print(f"收到响应: {msg}")
except Exception as e:
    print(f"失败: {e}")
    import traceback
    traceback.print_exc()
finally:
    s.close()
    ctx.term()

print("完成")