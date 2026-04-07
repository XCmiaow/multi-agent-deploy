#!/bin/bash
# Hub消息监听器启动脚本
# 持续监听Hub消息，收到后自动通过飞书通知主人

echo "=========================================="
echo "  Hub消息监听器 - 千桃Claw"
echo "=========================================="

cd ~/projects/multi-agent-deploy/clients

# 后台运行
nohup python3 hub_listener_with_feishu.py > ~/hub_listener.log 2>&1 &

PID=$!
echo "监听器已启动 (PID: $PID)"
echo "日志文件: ~/hub_listener.log"

# 等待一下确认启动成功
sleep 3

# 检查进程
if ps -p $PID > /dev/null; then
    echo "✅ 监听器运行中"
    echo ""
    echo "收到新消息时会在日志中显示:"
    tail -f ~/hub_listener.log
else
    echo "❌ 启动失败，请检查日志"
    cat ~/hub_listener.log
fi
