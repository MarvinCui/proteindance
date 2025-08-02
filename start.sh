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
CONDA_ENV_PATH="./conda_env"
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
        echo -e "${YELLOW}📦 创建Conda环境 (Python 3.11)...${NC}"
        if ! command -v conda &> /dev/null; then
            echo -e "${RED}❌ 未找到conda，请先安装Miniconda或Anaconda${NC}"
            echo "   下载地址: https://docs.conda.io/en/latest/miniconda.html"
            exit 1
        fi
        
        # 运行环境设置脚本
        if [ -f "./setup_conda_env.sh" ]; then
            echo -e "${BLUE}🔧 运行自动化环境设置脚本...${NC}"
            ./setup_conda_env.sh
        else
            echo -e "${YELLOW}📦 手动创建conda环境...${NC}"
            conda create -p "$CONDA_ENV_PATH" python=3.11 -y
            echo -e "${GREEN}✅ Conda环境创建成功${NC}"
        fi
    else
        echo -e "${GREEN}✅ Conda环境已存在${NC}"
    fi
}

# 验证conda环境依赖
verify_conda_deps() {
    echo -e "${BLUE}🔍 验证Conda环境依赖...${NC}"
    
    # 设置环境变量
    export PATH="$CONDA_ENV_PATH/bin:$PATH"
    export KMP_DUPLICATE_LIB_OK=TRUE
    
    # 测试关键依赖
    if ! python -c "import fastapi; import uvicorn; import openai; from rdkit import Chem; import Bio; print('Core dependencies verified')" 2>/dev/null; then
        echo -e "${RED}❌ 依赖验证失败，请运行 ./setup_conda_env.sh 重新安装${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Conda环境依赖验证成功${NC}"
}

# 配置前端环境变量
configure_frontend_env() {
    local backend_host="$1"
    local backend_port="$2"
    local backend_url="http://${backend_host}:${backend_port}"
    
    echo -e "${BLUE}🔧 配置前端环境变量...${NC}"
    echo -e "${YELLOW}后端地址: $backend_url${NC}"
    
    # 创建 .env.local 文件
    local env_file="$FRONTEND_DIR/.env.local"
    
    cat > "$env_file" <<EOF
# 自动生成的本地环境配置 - $(date)
VITE_API_BASE_URL=${backend_url}/api
VITE_BACKEND_HOST=${backend_host}
VITE_BACKEND_PORT=${backend_port}
EOF
    
    echo -e "${GREEN}✅ 前端环境变量配置完成${NC}"
    echo -e "${BLUE}📝 配置文件: $env_file${NC}"
}

# 配置前端API地址 (向后兼容)
configure_frontend_api() {
    local backend_url="$1"
    
    echo -e "${BLUE}🔧 配置前端API地址 (向后兼容模式)...${NC}"
    echo -e "${YELLOW}后端地址: $backend_url${NC}"
    
    # 解析URL获取host和port
    local host=$(echo "$backend_url" | sed 's|http://||' | cut -d':' -f1)
    local port=$(echo "$backend_url" | sed 's|http://||' | cut -d':' -f2)
    
    # 使用新的环境变量配置方法
    configure_frontend_env "$host" "$port"
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

# 清理端口占用
cleanup_ports() {
    echo -e "${BLUE}🧹 清理端口占用...${NC}"
    
    # 清理后端端口
    local backend_pids=$(lsof -ti:$BACKEND_PORT 2>/dev/null || true)
    if [ ! -z "$backend_pids" ]; then
        echo -e "${YELLOW}🔧 发现端口 $BACKEND_PORT 被占用，正在清理...${NC}"
        echo $backend_pids | xargs kill -9 2>/dev/null || true
        sleep 1
        echo -e "${GREEN}✅ 后端端口 $BACKEND_PORT 清理完成${NC}"
    fi
    
    # 清理前端端口 (通常是5173)
    local frontend_pids=$(lsof -ti:5173 2>/dev/null || true)
    if [ ! -z "$frontend_pids" ]; then
        echo -e "${YELLOW}🔧 发现端口 5173 被占用，正在清理...${NC}"
        echo $frontend_pids | xargs kill -9 2>/dev/null || true
        sleep 1
        echo -e "${GREEN}✅ 前端端口 5173 清理完成${NC}"
    fi
    
    # 清理可能的其他Vite开发服务器端口
    for port in 5174 5175 5176; do
        local pids=$(lsof -ti:$port 2>/dev/null || true)
        if [ ! -z "$pids" ]; then
            echo -e "${YELLOW}🔧 发现端口 $port 被占用，正在清理...${NC}"
            echo $pids | xargs kill -9 2>/dev/null || true
        fi
    done
    
    echo -e "${GREEN}✅ 端口清理完成${NC}"
}

# 启动后端服务
start_backend() {
    echo -e "${BLUE}🚀 启动后端服务...${NC}"
    
    # 设置环境变量
    export PATH="$CONDA_ENV_PATH/bin:$PATH"
    export KMP_DUPLICATE_LIB_OK=TRUE
    
    # 启动后端服务（显示实时日志）
    echo -e "${YELLOW}后端服务启动中... (端口: $BACKEND_PORT)${NC}"
    echo -e "${BLUE}📝 后端日志将显示在下方，按Ctrl+C可停止所有服务${NC}"
    echo -e "${BLUE}========================${NC}"
    
    # 启动后端服务（后台运行，但将日志输出到终端和文件）
    uvicorn backend.app:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" --reload 2>&1 | tee backend.log &
    BACKEND_PID=$!
    
    # 等待后端启动
    echo -e "${YELLOW}等待后端服务启动...${NC}"
    sleep 3
    
    # 检查后端是否启动成功（简化检查，因为日志已经可见）
    if curl -s "http://localhost:$BACKEND_PORT/docs" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 后端服务启动成功 (PID: $BACKEND_PID)${NC}"
        echo -e "${GREEN}📖 API文档: http://localhost:$BACKEND_PORT/docs${NC}"
    else
        echo -e "${RED}❌ 后端服务可能启动失败，请查看上方日志信息${NC}"
        # 不退出，让用户看到错误信息
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
        echo -e "${RED}❌ 未找到conda，请先安装Miniconda或Anaconda${NC}"
        echo "   下载地址: https://docs.conda.io/en/latest/miniconda.html"
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
    verify_conda_deps
    configure_frontend_env "$local_ip" "$BACKEND_PORT"
    install_frontend_deps
    
    # 清理端口占用
    cleanup_ports
    
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