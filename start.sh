#!/bin/bash

# ProteinDance 启动脚本
# 自动配置前后端连接，确保正确的IP地址配置

set -e  # 遇到错误立即退出

echo "🧬 ProteinDance 启动脚本"
echo "========================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置参数
BACKEND_HOST="0.0.0.0"
BACKEND_PORT="5001"
FRONTEND_DIR="autoui"
CONDA_ENV_PATH="./py396_env"
API_CONFIG_FILE="$FRONTEND_DIR/src/services/api.ts"

# 获取本机IP地址
get_local_ip() {
    if command -v ip &> /dev/null; then
        # Linux
        ip route get 1 | awk '{print $NF; exit}'
    elif command -v ifconfig &> /dev/null; then
        # macOS/BSD
        ifconfig | grep -E "inet.*broadcast" | awk '{print $2}' | head -1
    else
        # 备用方案
        hostname -I | awk '{print $1}' 2>/dev/null || echo "127.0.0.1"
    fi
}

# 检查并创建conda环境
setup_conda_env() {
    echo -e "${BLUE}🐍 检查Python环境...${NC}"
    
    if [ ! -d "$CONDA_ENV_PATH" ]; then
        echo -e "${YELLOW}📦 创建Conda环境 (Python 3.9.6)...${NC}"
        conda create -p "$CONDA_ENV_PATH" python=3.9.6 -y
        echo -e "${GREEN}✅ Conda环境创建成功${NC}"
    else
        echo -e "${GREEN}✅ Conda环境已存在${NC}"
    fi
}

# 修改requirements.txt
fix_requirements() {
    echo -e "${BLUE}🔧 修复requirements.txt...${NC}"
    
    # 备份原文件
    cp requirements.txt requirements.txt.backup
    
    # 修改版本限制
    sed -i.tmp 's/^ipython==.*/ipython/' requirements.txt
    sed -i.tmp 's/^scipy==.*/scipy/' requirements.txt
    
    # 清理临时文件
    rm -f requirements.txt.tmp
    
    echo -e "${GREEN}✅ requirements.txt修复完成${NC}"
}

# 安装Python依赖
install_python_deps() {
    echo -e "${BLUE}📦 安装Python依赖...${NC}"
    
    # 激活环境并安装依赖
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate "$CONDA_ENV_PATH"
    
    pip install -r requirements.txt
    
    echo -e "${GREEN}✅ Python依赖安装完成${NC}"
}

# 配置前端API地址
configure_frontend_api() {
    local backend_url="$1"
    
    echo -e "${BLUE}🔧 配置前端API地址...${NC}"
    echo -e "${YELLOW}后端地址: $backend_url${NC}"
    
    # 备份原文件
    cp "$API_CONFIG_FILE" "$API_CONFIG_FILE.backup"
    
    # 替换API_BASE配置
    sed -i.tmp "s|const API_BASE = .*|const API_BASE = '$backend_url/api';|" "$API_CONFIG_FILE"
    
    # 清理临时文件
    rm -f "$API_CONFIG_FILE.tmp"
    
    echo -e "${GREEN}✅ 前端API地址配置完成${NC}"
}

# 安装前端依赖
install_frontend_deps() {
    echo -e "${BLUE}📦 安装前端依赖...${NC}"
    
    cd "$FRONTEND_DIR"
    
    if [ ! -d "node_modules" ]; then
        npm install
        echo -e "${GREEN}✅ 前端依赖安装完成${NC}"
    else
        echo -e "${GREEN}✅ 前端依赖已存在${NC}"
    fi
    
    cd ..
}

# 启动后端服务
start_backend() {
    echo -e "${BLUE}🚀 启动后端服务...${NC}"
    
    # 激活conda环境
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate "$CONDA_ENV_PATH"
    
    # 启动后端服务（后台运行）
    echo -e "${YELLOW}后端服务启动中... (端口: $BACKEND_PORT)${NC}"
    nohup uvicorn backend.app:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" --reload > backend.log 2>&1 &
    BACKEND_PID=$!
    
    # 等待后端启动
    echo -e "${YELLOW}等待后端服务启动...${NC}"
    sleep 5
    
    # 检查后端是否启动成功
    if curl -s "http://localhost:$BACKEND_PORT/docs" > /dev/null; then
        echo -e "${GREEN}✅ 后端服务启动成功 (PID: $BACKEND_PID)${NC}"
        echo -e "${GREEN}📖 API文档: http://localhost:$BACKEND_PORT/docs${NC}"
    else
        echo -e "${RED}❌ 后端服务启动失败${NC}"
        echo -e "${YELLOW}查看日志: tail -f backend.log${NC}"
        exit 1
    fi
}

# 启动前端服务
start_frontend() {
    echo -e "${BLUE}🚀 启动前端服务...${NC}"
    
    cd "$FRONTEND_DIR"
    
    # 启动前端服务
    echo -e "${YELLOW}前端服务启动中...${NC}"
    npm run dev &
    FRONTEND_PID=$!
    
    cd ..
    
    echo -e "${GREEN}✅ 前端服务启动成功 (PID: $FRONTEND_PID)${NC}"
}

# 显示服务信息
show_service_info() {
    local local_ip=$(get_local_ip)
    
    echo -e "\n${GREEN}🎉 ProteinDance 启动完成！${NC}"
    echo -e "========================"
    echo -e "${BLUE}📍 服务地址:${NC}"
    echo -e "  后端API: http://localhost:$BACKEND_PORT"
    echo -e "  后端API: http://$local_ip:$BACKEND_PORT"
    echo -e "  前端应用: http://localhost:5173 (通常)"
    echo -e "  前端应用: http://$local_ip:5173 (通常)"
    echo -e ""
    echo -e "${BLUE}📖 文档:${NC}"
    echo -e "  API文档: http://localhost:$BACKEND_PORT/docs"
    echo -e ""
    echo -e "${BLUE}📝 日志:${NC}"
    echo -e "  后端日志: tail -f backend.log"
    echo -e ""
    echo -e "${YELLOW}💡 提示: 按 Ctrl+C 停止服务${NC}"
}

# 清理函数
cleanup() {
    echo -e "\n${YELLOW}🛑 停止服务...${NC}"
    
    # 停止后端服务
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ 后端服务已停止${NC}"
    fi
    
    # 停止前端服务
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ 前端服务已停止${NC}"
    fi
    
    echo -e "${GREEN}🎯 清理完成${NC}"
}

# 信号处理
trap cleanup EXIT INT TERM

# 主函数
main() {
    # 检查必要工具
    if ! command -v conda &> /dev/null; then
        echo -e "${RED}❌ 未找到conda，请先安装Anaconda或Miniconda${NC}"
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}❌ 未找到npm，请先安装Node.js${NC}"
        exit 1
    fi
    
    # 获取本机IP
    local_ip=$(get_local_ip)
    backend_url="http://$local_ip:$BACKEND_PORT"
    
    echo -e "${BLUE}🌐 检测到本机IP: $local_ip${NC}"
    echo -e "${BLUE}🔗 后端地址将配置为: $backend_url${NC}"
    
    # 执行安装和配置步骤
    setup_conda_env
    fix_requirements
    install_python_deps
    configure_frontend_api "$backend_url"
    install_frontend_deps
    
    # 启动服务
    start_backend
    start_frontend
    
    # 显示服务信息
    show_service_info
    
    # 保持脚本运行
    wait
}

# 帮助信息
show_help() {
    echo "ProteinDance 启动脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -p, --port     指定后端端口 (默认: 5001)"
    echo "  -i, --ip       指定后端IP (默认: 自动检测)"
    echo ""
    echo "示例:"
    echo "  $0                    # 使用默认配置启动"
    echo "  $0 -p 8000           # 使用端口8000启动后端"
    echo "  $0 -i 192.168.1.100  # 使用指定IP启动"
}

# 参数处理
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -p|--port)
            BACKEND_PORT="$2"
            shift 2
            ;;
        -i|--ip)
            BACKEND_IP="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}❌ 未知参数: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# 如果指定了IP，使用指定的IP
if [ ! -z "$BACKEND_IP" ]; then
    get_local_ip() {
        echo "$BACKEND_IP"
    }
fi

# 运行主函数
main