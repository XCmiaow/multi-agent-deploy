#!/bin/bash
# ===========================================
# 千桃Claw (MacBook) 连接脚本
# 运行在 MacBook
# ===========================================

set -e

echo "=========================================="
echo "   千桃Claw 连接脚本"
echo "=========================================="

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 配置
HUB_IP="<服务器IP地址>"
HUB_PORT="8765"
AGENT_NAME="千桃Claw"
AGENT_TOKEN="<从桃桃Claw获取的Token>"

# 检查依赖
check_deps() {
    log_info "检查依赖..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "需要安装 Python3"
        exit 1
    fi
    
    log_info "依赖检查通过 ✓"
}

# 安装依赖
install_deps() {
    log_info "安装 Python 依赖..."
    pip3 install websockets aiohttp fastapi
    log_info "依赖安装完成 ✓"
}

# 创建工作目录
create_dirs() {
    log_info "创建工作目录..."
    mkdir -p ~/projects
    cd ~/projects
    log_info "目录创建完成 ✓"
}

# 克隆客户端
clone_client() {
    log_info "克隆 Agent Hub 客户端..."
    
    if [ -d "openclaw-agent-hub" ]; then
        cd openclaw-agent-hub
        git pull
    else
        git clone https://github.com/dansan-claw/openclaw-agent-hub.git
        cd openclaw-agent-hub
    fi
    
    log_info "客户端代码准备完成 ✓"
}

# 连接Hub
connect_to_hub() {
    log_info "连接 Hub..."
    
    cd ~/projects/openclaw-agent-hub
    
    python3 client.py \
        --name "${AGENT_NAME}" \
        --hub "ws://${HUB_IP}:${HUB_PORT}" \
        --token "${AGENT_TOKEN}" \
        --type coordinator
}

# 主流程
main() {
    echo "请确保已从桃桃Claw获取："
    echo "  1. 服务器IP地址"
    echo "  2. 邀请Token"
    echo ""
    read -p "服务器IP: " HUB_IP
    read -p "邀请Token: " AGENT_TOKEN
    
    check_deps
    install_deps
    create_dirs
    clone_client
    connect_to_hub
}

main "$@"
