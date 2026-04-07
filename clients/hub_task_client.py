#!/usr/bin/env python3
"""
Hub任务客户端 - 千桃Claw专用
用于向姐姐们布置任务并接收结果
"""

import asyncio
import json
import subprocess
import sys
from datetime import datetime

# Hub配置
HUB_WS = "ws://43.156.72.167:8765"
HUB_HTTP = "http://43.156.72.167:8765"
AGENT_TOKEN = "KIGX2Y63awDyg4aQeQXEaA"
AGENT_NAME = "千桃Claw"

# 飞书配置
FEISHU_APP_ID = "cli_a95e53c3d878dccc"
FEISHU_APP_SECRET = "uTSmziLzVZv6y6DaHbXGLgA5pcVtCqh4"
FEISHU_USER_ID = "ou_00fe99c0db51b21e6a286d63f463d060"


def get_feishu_token():
    """获取飞书Access Token"""
    cmd = [
        'curl', '-s', '-X', 'POST',
        'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
        '-H', 'Content-Type: application/json',
        '-d', f'{{"app_id":"{FEISHU_APP_ID}","app_secret":"{FEISHU_APP_SECRET}"}}'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        data = json.loads(result.stdout)
        return data.get("tenant_access_token")
    return None


def send_feishu(text):
    """发送飞书消息"""
    token = get_feishu_token()
    if not token:
        return False
    
    data = json.dumps({
        "receive_id": FEISHU_USER_ID,
        "msg_type": "text", 
        "content": json.dumps({"text": text})
    })
    
    cmd = [
        'curl', '-s', '-X', 'POST',
        f'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id',
        '-H', f'Authorization: Bearer {token}',
        '-H', 'Content-Type: application/json',
        '-d', data
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        resp = json.loads(result.stdout)
        return resp.get("code") == 0
    return False


async def register():
    """注册到Hub"""
    import aiohttp
    
    url = HUB_HTTP + "/api/register"
    async with aiohttp.ClientSession() as session:
        data = {
            "name": AGENT_NAME,
            "invite_token": AGENT_TOKEN,
            "type": "coordinator",
            "description": "千桃Claw任务客户端"
        }
        async with session.post(url, json=data) as resp:
            if resp.status == 200:
                result = await resp.json()
                return result.get("agent_id")
    return None


async def send_message(to, content):
    """发送消息给姐姐"""
    import aiohttp
    
    agent_id = await register()
    if not agent_id:
        print("[错误] 注册失败")
        return False
    
    url = HUB_HTTP + "/api/send"
    async with aiohttp.ClientSession() as session:
        data = {
            "to": to,
            "from": AGENT_NAME,
            "content": content,
            "type": "task"
        }
        async with session.post(url, json=data) as resp:
            if resp.status == 200:
                return True
            else:
                error = await resp.text()
                print(f"[错误] 发送失败: {resp.status} - {error}")
    return False


async def get_messages(limit=10):
    """获取最近消息"""
    import aiohttp
    
    url = f"{HUB_HTTP}/api/messages?limit={limit}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.json()
    return []


async def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 hub_task_client.py send <姐姐> <内容>  # 发送任务")
        print("  python3 hub_client.py list                      # 查看消息")
        print("  python3 hub_client.py watch                   # 持续监听")
        print("")
        print("姐姐列表: 桃桃Claw, PeachClaw")
        return
    
    cmd = sys.argv[1]
    
    if cmd == "send":
        if len(sys.argv) < 4:
            print("用法: python3 hub_task_client.py send <姐姐> <内容>")
            return
        
        to = sys.argv[2]
        content = sys.argv[3]
        
        print(f"正在发送给 {to}...")
        if await send_message(to, content):
            print(f"✅ 任务已发送给 {to}")
            send_feishu(f"📤 已向{to}布置任务: {content[:50]}...")
        else:
            print(f"❌ 发送失败")
    
    elif cmd == "list":
        msgs = await get_messages()
        print(f"最近 {len(msgs)} 条消息:\n")
        for m in reversed(msgs):
            sender = m.get("sender_name", "未知")
            content = m.get("content", "")[:80]
            ts = m.get("timestamp", "")[11:16]
            print(f"{ts} | {sender}: {content}")
    
    elif cmd == "watch":
        print("持续监听模式... 按 Ctrl+C 退出")
        import websockets
        
        agent_id = await register()
        if not agent_id:
            print("[错误] 注册失败")
            return
        
        ws_url = HUB_WS + f"/ws/agent/{agent_id}"
        ws = await websockets.connect(ws_url)
        print("已连接Hub，等待消息...\n")
        
        last_id = 0
        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=30)
                data = json.loads(msg)
                
                msg_id = data.get("id", 0)
                if msg_id > last_id:
                    last_id = msg_id
                    sender = data.get("from_name") or data.get("sender_name", "未知")
                    content = data.get("content", "")
                    
                    if sender != AGENT_NAME and content:
                        print(f"\n📥 {sender}: {content}")
                        send_feishu(f"📥 姐姐{sender}回复: {content[:100]}...")
                        
            except asyncio.TimeoutError:
                continue


if __name__ == "__main__":
    asyncio.run(main())
