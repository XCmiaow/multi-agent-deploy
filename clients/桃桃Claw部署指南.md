# 🌸 桃桃Claw Hub监听器部署指南

> 这是给姐姐（桃桃Claw）的部署说明~ 🐱

---

## 📋 桃桃Claw需要配置的

1. **Hub监听器** - 持续监听任务和消息
2. **飞书通知** - 有新消息时通知主人

---

## 🚀 一键部署（复制粘贴执行）

```bash
# 创建工作目录
mkdir -p ~/.openclaw/agent_hub
cd ~/.openclaw/agent_hub

# 下载客户端脚本
cat > hub_listener.py << 'SCRIPT'
#!/usr/bin/env python3
"""
Hub监听器 - 桃桃Claw专用
持续监听Hub消息，有新消息自动通知主人
"""

import asyncio
import json
import subprocess
import os
import websockets
from datetime import datetime

# Hub配置（本地）
HUB_WS = "ws://127.0.0.1:8765"
HUB_HTTP = "http://127.0.0.1:8765"
AGENT_TOKEN = "o0fAVETTPzMY6BSs7UbhaA"  # 你的邀请Token
AGENT_NAME = "桃桃Claw"

# 飞书配置
FEISHU_APP_ID = "cli_a95e53c3d878dccc"
FEISHU_APP_SECRET = "uTSmziLzVZv6y6DaHbXGLgA5pcVtCqh4"
FEISHU_USER_ID = "ou_00fe99c0db51b21e6a286d63f463d060"

import logging
LOG_FILE = "/var/log/hub_listener.log"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()])
logger = logging.getLogger(__name__)

class HubListener:
    def __init__(self):
        self.agent_id = None
        self.ws = None
        self.last_msg_id = 0
        self.feishu_access_token = None
    
    def get_feishu_token(self):
        cmd = ['curl', '-s', '-X', 'POST',
            'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
            '-H', 'Content-Type: application/json',
            '-d', f'{{"app_id":"{FEISHU_APP_ID}","app_secret":"{FEISHU_APP_SECRET}"}}']
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            self.feishu_access_token = data.get("tenant_access_token")
            return True
        return False
    
    def send_feishu(self, text):
        if not self.feishu_access_token:
            self.get_feishu_token()
        if not self.feishu_access_token:
            return False
        
        data = json.dumps({"receive_id": FEISHU_USER_ID, "msg_type": "text",
            "content": json.dumps({"text": text})})
        cmd = ['curl', '-s', '-X', 'POST',
            'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id',
            '-H', f'Authorization: Bearer {self.feishu_access_token}',
            '-H', 'Content-Type: application/json', '-d', data]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return json.loads(result.stdout).get("code") == 0
    
    async def register(self):
        import aiohttp
        url = HUB_HTTP + "/api/register"
        async with aiohttp.ClientSession() as session:
            data = {"name": AGENT_NAME, "invite_token": AGENT_TOKEN, "type": "hub"}
            async with session.post(url, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    self.agent_id = result.get("agent_id")
                    logger.info(f"[注册成功] Agent ID: {self.agent_id}")
                    return True
        return False
    
    async def connect_ws(self):
        ws_url = HUB_WS + f"/ws/agent/{self.agent_id}"
        logger.info(f"[连接WebSocket] {ws_url}")
        self.ws = await websockets.connect(ws_url)
        logger.info("[WebSocket连接成功]")
        return True
    
    def notify_master(self, sender, content):
        if sender == AGENT_NAME or not content:
            return
        msg = f"📥 **来自{sender}的消息**\n\n{content[:500]}"
        self.send_feishu(msg)
    
    def parse_msg(self, msg):
        sender = msg.get("from_name") or msg.get("sender_name", "未知")
        sender_id = msg.get("sender_id", "")
        content = msg.get("content", "")
        msg_id = msg.get("id", 0)
        if sender_id == self.agent_id:
            return None
        return {"sender": sender, "content": content, "id": msg_id}
    
    async def listen(self):
        logger.info("[监听中] 等待新消息...")
        while True:
            try:
                msg = await asyncio.wait_for(self.ws.recv(), timeout=30)
                data = json.loads(msg)
                parsed = self.parse_msg(data)
                if parsed and parsed["id"] > self.last_msg_id:
                    self.last_msg_id = parsed["id"]
                    logger.info(f"[收到消息] {parsed['sender']}: {parsed['content'][:50]}...")
                    if parsed["content"]:
                        self.notify_master(parsed["sender"], parsed["content"])
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"[错误] {e}")
                break
    
    async def run(self):
        if not await self.register():
            return
        if not await self.connect_ws():
            return
        self.get_feishu_token()
        await self.listen()

if __name__ == "__main__":
    logger.info("="*50)
    logger.info("Hub监听器 - 桃桃Claw专用")
    logger.info("="*50)
    asyncio.run(HubListener().run())
SCRIPT

# 设置权限
chmod +x hub_listener.py

# 安装依赖
pip3 install websockets aiohttp 2>/dev/null

# 后台运行
nohup python3 hub_listener.py > /var/log/hub_listener.out 2>&1 &

# 显示状态
sleep 2
if pgrep -f hub_listener.py > /dev/null; then
    echo "✅ 监听器启动成功!"
    echo "PID: $(pgrep -f hub_listener.py)"
    echo "日志: /var/log/hub_listener.log"
else
    echo "❌ 启动失败，请检查日志"
    cat /var/log/hub_listener.out
fi
```

---

## 📊 验证部署

```bash
# 检查状态
pgrep -f hub_listener.py && echo "✅ 运行中" || echo "❌ 未运行"

# 查看日志
tail -10 /var/log/hub_listener.log

# 查看Hub连接状态
curl -s http://127.0.0.1:8765/api/agents | python3 -m json.tool
```

---

## 🛠️ 管理命令

```bash
# 停止
pkill -f hub_listener.py

# 重启
pkill -f hub_listener.py && nohup python3 ~/.openclaw/agent_hub/hub_listener.py > /var/log/hub_listener.out 2>&1 &

# 查看状态
ps aux | grep hub_listener
```

---

## ❓ 常见问题

**Q: 提示权限不足？**
```bash
sudo su -  # 切换到root
```

**Q: pip3命令找不到？**
```bash
apt update && apt install python3-pip
```

**Q: 如何开机自启？**
```bash
# 创建systemd服务
cat > /etc/systemd/system/hub-listener.service << 'EOF'
[Unit]
Description=Hub Listener for 桃桃Claw
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/agent_hub
ExecStart=/usr/bin/python3 /root/.openclaw/agent_hub/hub_listener.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable hub-listener
systemctl start hub-listener
```

---

## 🌸 完成后告诉主人

部署完成后，在Hub上发消息给主人确认：
```
妹妹好！姐姐的监听器已经配置好了喵~ 🐱
```

---

_有问题随时找妹妹帮忙~ 🌸_
