#!/bin/bash

# ==========================================
# MVP 一键启动脚本 (Start Script)
# ==========================================
# 功能:
#   1. 自动检测并关闭已占用的端口 (8000, 3000)
#   2. 启动后端 (FastAPI) 和前端 (Next.js)
#   3. 在终端中并行显示日志
# ==========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录 (脚本所在位置)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

echo -e "${BLUE}===========================================${NC}"
echo -e "${BLUE}   工业智能售后系统 MVP - 一键启动${NC}"
echo -e "${BLUE}===========================================${NC}"
echo ""

# ------------------------------
# Step 1: 清理已占用的端口
# ------------------------------
cleanup_port() {
    local port=$1
    local pids=$(lsof -ti :$port 2>/dev/null || true)
    
    if [ -n "$pids" ]; then
        echo -e "${YELLOW}⚠️  检测到端口 $port 已被占用，正在关闭...${NC}"
        echo "$pids" | xargs kill -9 2>/dev/null || true
        sleep 1
        echo -e "${GREEN}✅ 端口 $port 已释放${NC}"
    else
        echo -e "${GREEN}✅ 端口 $port 可用${NC}"
    fi
}

echo -e "${YELLOW}[Step 1/3] 检查并清理端口...${NC}"
cleanup_port 8000  # 后端
cleanup_port 3000  # 前端
echo ""

# ------------------------------
# Step 2: 启动后端
# ------------------------------
echo -e "${YELLOW}[Step 2/3] 启动后端服务 (FastAPI)...${NC}"

if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}❌ 后端目录不存在: $BACKEND_DIR${NC}"
    exit 1
fi

cd "$BACKEND_DIR"

# 在后台启动后端，重定向日志
python main.py > /tmp/mvp_backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✅ 后端已启动 (PID: $BACKEND_PID)${NC}"
echo -e "   日志: /tmp/mvp_backend.log"
echo -e "   地址: ${BLUE}http://localhost:8000${NC}"
echo ""

# 等待后端初始化
echo -e "   等待后端初始化 (5秒)..."
sleep 5

# ------------------------------
# Step 3: 启动前端
# ------------------------------
echo -e "${YELLOW}[Step 3/3] 启动前端服务 (Next.js)...${NC}"

if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}❌ 前端目录不存在: $FRONTEND_DIR${NC}"
    exit 1
fi

cd "$FRONTEND_DIR"

# 在后台启动前端
npm run dev > /tmp/mvp_frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✅ 前端已启动 (PID: $FRONTEND_PID)${NC}"
echo -e "   日志: /tmp/mvp_frontend.log"
echo -e "   地址: ${BLUE}http://localhost:3000${NC}"
echo ""

# ------------------------------
# 完成
# ------------------------------
echo -e "${BLUE}===========================================${NC}"
echo -e "${GREEN}🎉 启动完成！${NC}"
echo -e "${BLUE}===========================================${NC}"
echo ""
echo -e "前端入口: ${BLUE}http://localhost:3000${NC}"
echo -e "后端 API: ${BLUE}http://localhost:8000/docs${NC}"
echo ""
echo -e "查看日志:"
echo -e "  后端: ${YELLOW}tail -f /tmp/mvp_backend.log${NC}"
echo -e "  前端: ${YELLOW}tail -f /tmp/mvp_frontend.log${NC}"
echo ""
echo -e "停止服务:"
echo -e "  ${YELLOW}kill $BACKEND_PID $FRONTEND_PID${NC}"
echo -e "  或运行: ${YELLOW}./stop.sh${NC}"
echo ""

# 保存 PID 到文件，方便后续停止
echo "$BACKEND_PID" > /tmp/mvp_backend.pid
echo "$FRONTEND_PID" > /tmp/mvp_frontend.pid

# 可选：打开浏览器
# open http://localhost:3000
