#!/bin/bash

# ProteinDance Docker 启动脚本
# 端口映射和容器管理

echo "🧬 Starting ProteinDance Docker Container..."

# 停止现有容器（如果存在）
echo "🛑 Stopping existing containers..."
docker stop proteindance 2>/dev/null || true
docker rm proteindance 2>/dev/null || true

# 启动新容器，映射端口
echo "🚀 Starting new container with port mapping..."
docker run -d \
  --name proteindance \
  --restart unless-stopped \
  -p 5001:5001 \
  -p 5173:5173 \
  -v "$(pwd)/proteindance.db:/app/proteindance.db" \
  -v "$(pwd)/backend/logs:/app/backend/logs" \
  proteindance:latest

# 等待容器启动
echo "⏳ Waiting for services to start..."
sleep 10

# 检查容器状态
echo "📊 Container Status:"
docker ps | grep proteindance

# 显示日志
echo -e "\n📝 Recent logs:"
docker logs proteindance --tail 20

# 访问链接
echo -e "\n✅ ProteinDance is now running!"
echo "🔗 Access URLs:"
echo "   Frontend App: http://localhost:5173"
echo "   Backend API:  http://localhost:5001"
echo "   API Docs:     http://localhost:5001/docs"
echo ""
echo "🛠  Management Commands:"
echo "   View logs:    docker logs proteindance -f"
echo "   Stop:         docker stop proteindance"
echo "   Restart:      docker restart proteindance"
echo "   Shell access: docker exec -it proteindance /bin/bash"