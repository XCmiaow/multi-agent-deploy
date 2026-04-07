#!/usr/bin/env python3
"""
Hub消息监听器 - 持续监听Hub消息并通过飞书报告
收到新消息时自动通知主人
使用curl发送飞书消息避免SSL问题
"""

import asyncio
import json
import subprocess
import os
import websockets
from datetime import datetime
import logging

# Hub配置
HUB_WS = "ws://43.156.72.167:8765"
HUB_HTTP = "http://43.156.72.167:8765"
AGENT_TOKEN = "KIGX2Y63awDyg4aQeQXEaA"
AGENT_NAME = "千桃Claw"

# 飞书配置
FEISHU_APP_ID = "cli_a95e53c3d878dccc"
FEISHU_APP_SECRET = "uTSmziLzVZv6y6DaHbXGLgA5pcVtCqh4"
FEISHU_USER_ID = "ou_00fe99c0db51b21e6a286d63f463d060"

# 日志配置
LOG_FILE = os.path.expanduser("~/hub_listener.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class HubListener:
    def __init__(self):
        self.agent_id = None
        self.ws = None
        self.last_msg_id = 0
        self.running = True
        self.feishu_access_token = None
    
    def get_feishu_token(self):
        """获取飞书Access Token - 使用curl"""
        cmd = [
            'curl', '-s', '-X', 'POST',
            'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
            '-H', 'Content-Type: application/json',
            '-d', f'{{"app_id":"{FEISHU_APP_ID}","app_secret":"{FEISHU_APP_SECRET}"}}'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                self.feishu_access_token = data.get("tenant_access_token")
                if self.feishu_access_token:
                    logger.info("[飞书] Access Token获取成功")
                    return True
            logger.error(f"[飞书] Token获取失败: {result.stderr}")
            return False
        except Exception as e:
            logger.error(f"[飞书] Token获取异常: {e}")
            return False
    
    def send_feishu_message(self, text):
        """发送飞书消息给主人 - 使用curl"""
        if not self.feishu_access_token:
            self.get_feishu_token()
        
        if not self.feishu_access_token:
            logger.warning("[飞书] 无法发送：无Token")
            return False
        
        cmd = [
            'curl', '-s', '-X', 'POST',
            'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id',
            '-H', f'Authorization: Bearer {self.feishu_access_token}',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps({
                "receive_id": FEISHU_USER_ID,
                "msg_type": "text",
                "content": json.dumps({"text": text})
            })
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data.get("code") == 0:
                    logger.info("[飞书] 消息发送成功")
                    return True
                else:
                    logger.error(f"[飞书] 发送失败: {data.get('msg')}")
                    # Token过期则重新获取
                    if data.get("code") == 99991664:
                        self.feishu_access_token = None
                    return False
            logger.error(f"[飞书] 发送失败: {result.stderr}")
            return False
        except Exception as e:
            logger.error(f"[飞书] 发送异常: {e}")
            return False
    
    async def register(self):
        """注册到Hub"""
        import aiohttp
        
        url = HUB_HTTP + "/api/register"
        async with aiohttp.ClientSession() as session:
            data = {
                "name": AGENT_NAME,
                "invite_token": AGENT_TOKEN,
                "type": "coordinator",
                "description": "Hub消息监听器，持续监听并报告"
            }
            async with session.post(url, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    self.agent_id = result.get("agent_id")
                    logger.info(f"[注册成功] Agent ID: {self.agent_id}")
                    return True
                else:
                    logger.error(f"[注册失败] {resp.status}")
                    return False
    
    async def connect_websocket(self):
        """连接WebSocket"""
        ws_url = HUB_WS + f"/ws/agent/{self.agent_id}"
        logger.info(f"[连接WebSocket] {ws_url}")
        self.ws = await websockets.connect(ws_url)
        logger.info("[WebSocket连接成功]")
        return True
    
    def notify_master(self, sender, content):
        """通知主人"""
        if not content or sender == AGENT_NAME:
            return
        
        # 构造通知消息
        msg = f"📥 **新消息通知**\n\n"
        msg += f"👤 来自: **{sender}**\n\n"
        msg += f"📝 内容:\n{content[:800]}"
        
        self.send_feishu_message(msg)
    
    def parse_message(self, msg):
        """解析消息"""
        msg_type = msg.get("type", "")
        sender = msg.get("from_name") or msg.get("sender_name", "未知")
        sender_id = msg.get("sender_id", "")
        content = msg.get("content", "")
        msg_id = msg.get("id", 0)
        
        # 跳过自己发送的消息
        if sender_id == self.agent_id:
            return None
        
        return {
            "type": msg_type,
            "sender": sender,
            "content": content,
            "id": msg_id
        }
    
    async def listen(self):
        """持续监听消息"""
        logger.info("[监听中] 等待新消息...")
        
        while self.running:
            try:
                msg = await asyncio.wait_for(self.ws.recv(), timeout=30)
                data = json.loads(msg)
                
                parsed = self.parse_message(data)
                if parsed and parsed["id"] > self.last_msg_id:
                    self.last_msg_id = parsed["id"]
                    
                    content = parsed["content"] or "(无文字内容)"
                    logger.info(f"[收到消息] {parsed['sender']}: {content[:50]}...")
                    
                    # 如果是任务消息，通过飞书通知主人
                    if parsed["content"]:
                        self.notify_master(parsed["sender"], parsed["content"])
                        
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosed:
                logger.warning("[连接断开] 尝试重连...")
                break
            except Exception as e:
                logger.error(f"[错误] {e}")
                break
    
    async def run(self):
        """运行主流程"""
        # 注册
        if not await self.register():
            return
        
        # 连接WebSocket
        if not await self.connect_websocket():
            return
        
        # 获取飞书Token
        self.get_feishu_token()
        
        # 持续监听
        await self.listen()

async def main():
    logger.info("="*50)
    logger.info("Hub消息监听器 - 千桃Claw专用")
    logger.info("="*50)
    
    listener = HubListener()
    await listener.run()

if __name__ == "__main__":
    asyncio.run(main())
