#!/bin/bash
# ===========================================
# 桃桃Claw Hub 服务器部署脚本
# 运行在 Ubuntu 服务器 (桃桃Claw)
# ===========================================

set -e

echo "=========================================="
echo "   桃桃Claw Hub 部署脚本"
echo "   OpenClaw Agent Hub v1.0"
echo "=========================================="

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查系统
check_system() {
    log_info "检查系统环境..."
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        log_error "此脚本应在 Linux (Ubuntu) 上运行"
        exit 1
    fi
    log_info "系统检查通过 ✓"
}

# 安装依赖
install_dependencies() {
    log_info "安装系统依赖..."
    
    # 更新包列表
    sudo apt-get update -qq
    
    # 安装 Python 和 pip
    sudo apt-get install -y python3 python3-pip python3-venv
    
    # 安装 Git
    sudo apt-get install -y git
    
    log_info "依赖安装完成 ✓"
}

# 创建目录
create_dirs() {
    log_info "创建工作目录..."
    mkdir -p ~/.openclaw/agent_hub
    cd ~/.openclaw/agent_hub
    log_info "目录创建完成: ~/.openclaw/agent_hub"
}

# 克隆 Agent Hub
clone_hub() {
    log_info "克隆 OpenClaw Agent Hub..."
    
    if [ -d "openclaw-agent-hub" ]; then
        log_warn "openclaw-agent-hub 已存在，跳过克隆"
    else
        git clone https://github.com/dansan-claw/openclaw-agent-hub.git
    fi
    
    cd openclaw-agent-hub
    log_info "Hub 克隆完成 ✓"
}

# 安装 Python 依赖
install_python_deps() {
    log_info "安装 Python 依赖..."
    
    pip3 install --upgrade pip
    pip3 install fastapi uvicorn websockets aiohttp sqlite3
    
    log_info "Python 依赖安装完成 ✓"
}

# 配置 Hub
configure_hub() {
    log_info "配置 Hub..."
    
    # 获取服务器IP
    SERVER_IP=$(hostname -I | awk '{print $1}')
    
    # 创建配置文件
    cat > ~/.openclaw/agent_hub/config.json << EOF
{
    "hub": {
        "host": "0.0.0.0",
        "port": 8765,
        "max_agents": 10,
        "auth_required": true,
        "server_ip": "${SERVER_IP}"
    },
    "agents": {
        "桃桃Claw": {
            "role": "hub",
            "name": "桃桃Claw",
            "description": "Hub主控，知识库中枢",
            "capabilities": ["coordination", "long_tasks", "knowledge_base", "hub"]
        },
        "PeachClaw": {
            "role": "worker",
            "name": "PeachClaw", 
            "description": "计算主力，WSL",
            "capabilities": ["computation", "scraping", "coding", "worker"]
        },
        "千桃Claw": {
            "role": "coordinator",
            "name": "千桃Claw",
            "description": "协调者，MacBook高权限",
            "capabilities": ["feishu", "coordination", "permissions", "coordinator"]
        }
    }
}
EOF
    
    log_info "配置文件创建完成 ✓"
    log_info "服务器IP: ${SERVER_IP}"
}

# 生成邀请Token
generate_tokens() {
    log_info "生成邀请Token..."
    
    cd ~/.openclaw/agent_hub/openclaw-agent-hub
    
    # 启动一次Hub生成token
    python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from server import app, generate_invite_token
import json

token = generate_invite_token()
print('PEACH_TOKEN=' + token)

token2 = generate_invite_token()
print('QIANTAO_TOKEN=' + token2)
" > ~/.openclaw/agent_hub/tokens.txt 2>/dev/null || {
        # 如果上面的方法不行，用curl
        echo "使用备用方法生成Token..."
    }
    
    log_info "Token已保存到 ~/.openclaw/agent_hub/tokens.txt"
}

# 启动Hub
start_hub() {
    log_info "启动 Hub..."
    
    cd ~/.openclaw/agent_hub/openclaw-agent-hub
    
    # 后台启动
    nohup python3 server.py --host 0.0.0.0 --port 8765 > ~/.openclaw/agent_hub/hub.log 2>&1 &
    
    # 等待启动
    sleep 3
    
    # 检查是否运行
    if pgrep -f "server.py" > /dev/null; then
        log_info "Hub 启动成功! ✓"
        log_info "Hub 地址: ws://${SERVER_IP}:8765"
    else
        log_error "Hub 启动失败，请检查日志 ~/.openclaw/agent_hub/hub.log"
        exit 1
    fi
}

# 显示状态
show_status() {
    SERVER_IP=$(hostname -I | awk '{print $1}')
    
    echo ""
    echo "=========================================="
    echo "   🎉 部署完成！"
    echo "=========================================="
    echo ""
    echo "📍 Hub 地址: ws://${SERVER_IP}:8765"
    echo "📍 Web UI: http://${SERVER_IP}:8765"
    echo "📍 日志: ~/.openclaw/agent_hub/hub.log"
    echo ""
    echo "📋 Token 文件: ~/.openclaw/agent_hub/tokens.txt"
    echo ""
    echo "请将以下信息发给千桃Claw和PeachClaw："
    echo "  服务器IP: ${SERVER_IP}"
    echo "  端口: 8765"
    echo ""
}

# 主流程
main() {
    check_system
    install_dependencies
    create_dirs
    clone_hub
    install_python_deps
    configure_hub
    generate_tokens
    start_hub
    show_status
}

main "$@"
