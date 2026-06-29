#!/bin/bash
# 自动启动服务 + 隧道，断开自动重连
cd "/Users/apple/字符串替换"

# 启动 Flask 服务
lsof -ti :5100 | xargs kill -9 2>/dev/null
python3 server.py &
sleep 2
echo "✅ 服务器已启动: http://localhost:5100"

# 保持隧道连接，断开自动重连
while true; do
  echo "🔗 正在建立公网隧道..."
  ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes \
      -R 80:localhost:5100 nokey@localhost.run 2>&1 | while read line; do
    echo "$line"
    # 提取新URL
    if echo "$line" | grep -q "lhr.life"; then
      echo "$line" | grep -o 'https://[a-z0-9]*\.lhr\.life' > /tmp/current_url.txt
    fi
  done
  echo "⚠️ 隧道断开，5秒后重连..."
  sleep 5
done
