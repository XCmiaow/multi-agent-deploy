#!/usr/bin/env python3
"""
OpenClaw Agent Hub 客户端
支持连接 Hub 并进行消息收发
"""

import asyncio
import json
import sys
import argparse
from datetime import datetime
import websockets
import aiohttp

class OpenClawAgent:
    """简化的 OpenClaw Agent 客户端"""
    
    def __init__(self, name, hub_url, token, agent_type="custom", description=""):
        self.name = name
        self.hub_url = hub_url
        self.token = token
        self.agent_type = agent_type
        self.description = description
        self.ws = None
        self.connected = False
        self.agent_id = None
        
    async def register(self):
        """向Hub注册"""
        try:
            # 通过REST API注册
            async with aiohttp.ClientSession() as session:
                url = f"{self.hub_url}/api/register"
                data = {
                    "name": self.name,
                    "token": self.token,
                    "type": self.agent_type,
                    "description": self.description,
                    "capabilities": self._get_capabilities()
                }
                
                async with session.post(url, json=data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        self.agent_id = result.get("agent_id")
                        print(f"[注册成功] Agent ID: {self.agent_id}")
                        return True
                    else:
                        error = await resp.text()
                        print(f"[注册失败] {resp.status}: {error}")
                        return False
                        
        except Exception as e:
            print(f"[注册异常] {e}")
            return False
    
    async def connect_websocket(self):
        """通过WebSocket连接"""
        ws_url = self.hub_url.replace("http", "ws") + f"/ws/agent/{self.agent_id}"
        print(f"[连接WebSocket] {ws_url}")
        
        try:
            self.ws = await websockets.connect(ws_url)
            self.connected = True
            print(f"[WebSocket连接成功]")
            return True
        except Exception as e:
            print(f"[WebSocket连接失败] {e}")
            return False
    
    async def send_message(self, to, content, msg_type="chat"):
        """发送消息"""
        if not self.connected:
            print("[错误] 未连接Hub")
            return False
            
        message = {
            "type": msg_type,
            "to": to,
            "from": self.name,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            await self.ws.send(json.dumps(message))
            print(f"[发送消息] -> {to}: {content[:50]}...")
            return True
        except Exception as e:
            print(f"[发送失败] {e}")
            return False
    
    async def broadcast(self, content):
        """广播消息"""
        if not self.connected:
            print("[错误] 未连接Hub")
            return False
            
        message = {
            "type": "broadcast",
            "from": self.name,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            await self.ws.send(json.dumps(message))
            print(f"[广播消息] {content[:50]}...")
            return True
        except Exception as e:
            print(f"[广播失败] {e}")
            return False
    
    async def listen(self):
        """监听消息"""
        print(f"[监听中] 等待消息...")
        
        try:
            async for msg in self.ws:
                data = json.loads(msg)
                await self.handle_message(data)
        except Exception as e:
            print(f"[监听断开] {e}")
    
    async def handle_message(self, msg):
        """处理收到的消息"""
        msg_type = msg.get("type", "unknown")
        sender = msg.get("from", "unknown")
        content = msg.get("content", "")
        
        print(f"\n[收到消息] {sender}: {content}")
        
        # 根据消息类型处理
        if msg_type == "task":
            print(f"  -> 收到任务: {content}")
            # 可以在这里添加任务处理逻辑
        elif msg_type == "broadcast":
            print(f"  -> 广播: {content}")
    
    async def run(self):
        """运行主流程"""
        # 1. 注册
        if not await self.register():
            print("[错误] 注册失败，退出")
            return
        
        # 2. 连接WebSocket
        if not await self.connect_websocket():
            print("[错误] WebSocket连接失败，退出")
            return
        
        # 3. 监听消息
        await self.listen()
    
    def _get_capabilities(self):
        """获取Agent能力"""
        capabilities = {
            "coordinator": ["coordination", "task_dispatch", "feishu"],
            "worker": ["computation", "scraping", "coding"],
            "hub": ["coordination", "long_tasks", "knowledge_base"],
            "custom": ["general"]
        }
        return capabilities.get(self.agent_type, ["general"])


async def main():
    parser = argparse.ArgumentParser(description="OpenClaw Agent Hub 客户端")
    parser.add_argument("--name", required=True, help="Agent名称")
    parser.add_argument("--hub", required=True, help="Hub地址，如 ws://192.168.1.100:8765")
    parser.add_argument("--token", required=True, help="邀请Token")
    parser.add_argument("--type", default="custom", choices=["coordinator", "worker", "hub", "custom"], help="Agent类型")
    parser.add_argument("--description", default="", help="Agent描述")
    parser.add_argument("--send", help="发送消息后退出")
    parser.add_argument("--broadcast", help="广播消息后退出")
    
    args = parser.parse_args()
    
    agent = OpenClawAgent(
        name=args.name,
        hub_url=args.hub,
        token=args.token,
        agent_type=args.type,
        description=args.description
    )
    
    if args.send:
        # 只发送消息
        if await agent.register() and await agent.connect_websocket():
            target, msg = args.send.split(":", 1)
            await agent.send_message(target, msg)
        return
    
    if args.broadcast:
        # 只广播
        if await agent.register() and await agent.connect_websocket():
            await agent.broadcast(args.broadcast)
        return
    
    # 正常运行（监听模式）
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
