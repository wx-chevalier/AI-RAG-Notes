#!/bin/bash

# ==========================================
# MVP 一键停止脚本 (Stop Script)
# ==========================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}正在停止 MVP 服务...${NC}"

# 方法1: 通过保存的 PID 文件
if [ -f /tmp/mvp_backend.pid ]; then
    BACKEND_PID=$(cat /tmp/mvp_backend.pid)
    kill -9 $BACKEND_PID 2>/dev/null && echo -e "${GREEN}✅ 后端已停止 (PID: $BACKEND_PID)${NC}"
    rm -f /tmp/mvp_backend.pid
fi

if [ -f /tmp/mvp_frontend.pid ]; then
    FRONTEND_PID=$(cat /tmp/mvp_frontend.pid)
    kill -9 $FRONTEND_PID 2>/dev/null && echo -e "${GREEN}✅ 前端已停止 (PID: $FRONTEND_PID)${NC}"
    rm -f /tmp/mvp_frontend.pid
fi

# 方法2: 通过端口强制清理 (兜底)
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
lsof -ti :3000 | xargs kill -9 2>/dev/null || true

echo -e "${GREEN}🛑 所有服务已停止${NC}"
