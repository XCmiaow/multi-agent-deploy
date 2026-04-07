# 🌸 桃桃Claw三姐妹协作系统 - 部署指南

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Hub (任务协调中心)                         │
│              部署在: 桃桃Claw (Ubuntu服务器)                  │
│              地址: ws://<服务器IP>:8765                       │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ 桃桃Claw │          │PeachClaw│          │ 千桃Claw │
   │  Hub主控 │          │ WSL主力 │          │ MacBook │
   │ 24h在线 │          │晚上断电 │          │ 高权限  │
   └─────────┘          └─────────┘          └─────────┘
```

## 部署步骤

### 第一步：在桃桃Claw（服务器）部署Hub

**复制并运行以下命令：**

```bash
# 在桃桃Claw服务器上执行
mkdir -p ~/.openclaw/agent_hub
cd ~/.openclaw/agent_hub

# 下载部署脚本
curl -O https://raw.githubusercontent.com/XCmiaow/peach-claw-config/main/scripts/deploy-hub.sh
chmod +x deploy-hub.sh

# 运行部署
./deploy-hub.sh
```

部署成功后会显示：
- Hub地址 (ws://服务器IP:8765)
- 邀请Token (用于客户端连接)

---

### 第二步：PeachClaw (WSL) 连接

```bash
# 在PeachClaw上执行
mkdir -p ~/projects
cd ~/projects

# 下载客户端脚本
curl -O https://raw.githubusercontent.com/XCmiaow/peach-claw-config/main/scripts/connect-peachclaw.sh
chmod +x connect-peachclaw.sh

# 运行（会提示输入服务器IP和Token）
./connect-peachclaw.sh
```

---

### 第三步：千桃Claw (MacBook) 连接

```bash
# 在MacBook上执行
mkdir -p ~/projects
cd ~/projects

# 下载客户端脚本
curl -O https://raw.githubusercontent.com/XCmiaow/peach-claw-config/main/scripts/connect-qiatao.sh
chmod +x connect-qiatao.sh

# 运行
./connect-qiatao.sh
```

---

## 常用命令

### Hub 管理 (桃桃Claw)

```bash
# 查看Hub状态
curl http://localhost:8765/api/status

# 查看已连接的Agent
curl http://localhost:8765/api/agents

# 查看消息日志
curl http://localhost:8765/api/messages

# 生成新的邀请Token
curl -X POST http://localhost:8765/api/invite

# 停止Hub
pkill -f "python3 server.py"

# 重启Hub
cd ~/.openclaw/agent_hub/openclaw-agent-hub
nohup python3 server.py --host 0.0.0.0 --port 8765 > ../hub.log 2>&1 &
```

### 客户端连接测试

```bash
# PeachClaw 测试发送消息
python3 connect_client.py \
  --name "PeachClaw" \
  --hub "ws://服务器IP:8765" \
  --token "你的Token" \
  --type worker

# 千桃Claw 测试发送消息
python3 connect_client.py \
  --name "千桃Claw" \
  --hub "ws://服务器IP:8765" \
  --token "你的Token" \
  --type coordinator
```

---

## 消息协议

### 任务分发

```json
{
  "type": "task",
  "to": "PeachClaw",
  "content": {
    "title": "抓取小红书帖子",
    "command": "node scrape.js explore 50"
  }
}
```

### 状态报告

```json
{
  "type": "status",
  "from": "PeachClaw",
  "content": "busy"
}
```

### 任务交接

```json
{
  "type": "handover",
  "to": "桃桃Claw",
  "content": {
    "task_id": "xxx",
    "progress": "50%",
    "state": {"key": "value"}
  }
}
```

---

## 断电保护机制

### PeachClaw 关机前自动执行

```bash
# 保存当前任务状态
curl -X POST http://服务器IP:8765/api/message \
  -H "Content-Type: application/json" \
  -d '{"type":"handover","from":"PeachClaw","content":"正在执行任务，请接管"}'
```

### 桃桃Claw 接管任务

```bash
# 查看待接管任务
curl http://服务器IP:8765/api/messages?type=handover
```

---

## 故障排查

| 问题 | 解决方法 |
|------|----------|
| Hub无法启动 | 检查端口8765是否被占用 `lsof -i :8765` |
| 客户端连接失败 | 检查服务器IP和防火墙设置 |
| Token无效 | 重新生成 `curl -X POST http://localhost:8765/api/invite` |
| 消息发送失败 | 检查Agent是否在线 |

---

## 文件位置

- Hub数据: `~/.openclaw/agent_hub/`
- Hub日志: `~/.openclaw/agent_hub/hub.log`
- Token文件: `~/.openclaw/agent_hub/tokens.txt`
- 配置文件: `~/.openclaw/agent_hub/config.json`

---

_最后更新：2026-04-07_
