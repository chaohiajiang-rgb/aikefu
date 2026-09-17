#!/bin/bash
# run_local.sh — MES 智能客服 Mac 本机离线一键启动
#
# 顺序：本地模型(8001) → 等就绪 → FastAPI 后端(8000)
# 用法：
#   bash run_local.sh start          # 启动（默认）
#   bash run_local.sh stop           # 停止
#   bash run_local.sh restart        # 重启
#   bash run_local.sh status         # 查看状态
#   MES_MODEL=mlx-community/Qwen2.5-7B-Instruct-4bit bash run_local.sh start   # 换 7B
#
# 说明：
#   - 本地模型用系统 Python(.venv-sys) + `python -S` 跳过 WorkBuddy 注入的
#     sitecustomize 文件访问 broker；HF_HUB_ENABLE_HF_TRANSFER=1 多线程下载权重。
#   - 后端用 managed Python(.venv) 的 uvicorn。
#   - 模型/后端日志分别见 /tmp/mlx.log 和 /tmp/mescs.log。

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

MODEL="${MES_MODEL:-mlx-community/Qwen2.5-3B-Instruct-4bit}"
MODEL_PORT=8001
API_PORT=8000

start_model() {
  if lsof -i :$MODEL_PORT >/dev/null 2>&1; then
    echo "[跳过] 模型服务已在 $MODEL_PORT 运行"
    return 0
  fi
  echo "[1/2] 启动本地模型 $MODEL (端口 $MODEL_PORT)…"
  # macOS 无 setsid，有则用 setsid，否则回退 nohup
  if command -v setsid >/dev/null 2>&1; then
    setsid env HF_HUB_ENABLE_HF_TRANSFER=1 .venv-sys/bin/python -S start_model.py \
      --model "$MODEL" --port $MODEL_PORT --host 0.0.0.0 > /tmp/mlx.log 2>&1 < /dev/null &
  else
    nohup env HF_HUB_ENABLE_HF_TRANSFER=1 .venv-sys/bin/python -S start_model.py \
      --model "$MODEL" --port $MODEL_PORT --host 0.0.0.0 > /tmp/mlx.log 2>&1 < /dev/null &
  fi
  echo "      日志: /tmp/mlx.log"
}

wait_model() {
  echo "      等待模型服务就绪…"
  for i in $(seq 1 60); do
    if curl -s --max-time 5 -o /dev/null -w "%{http_code}" "http://localhost:$MODEL_PORT/v1/models" 2>/dev/null | grep -q 200; then
      echo "      ✓ 模型就绪"
      return 0
    fi
    sleep 5
  done
  echo "      ✗ 模型服务超时未就绪，请查看 /tmp/mlx.log"
  return 1
}

start_api() {
  if lsof -i :$API_PORT >/dev/null 2>&1; then
    echo "[跳过] 后端已在 $API_PORT 运行"
    return 0
  fi
  echo "[2/2] 启动 FastAPI 后端 (端口 $API_PORT)…"
  if command -v setsid >/dev/null 2>&1; then
    setsid .venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port $API_PORT > /tmp/mescs.log 2>&1 < /dev/null &
  else
    nohup .venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port $API_PORT > /tmp/mescs.log 2>&1 < /dev/null &
  fi
  echo "      日志: /tmp/mescs.log"
}

wait_api() {
  for i in $(seq 1 30); do
    if curl -s --max-time 5 -o /dev/null -w "%{http_code}" "http://localhost:$API_PORT/" 2>/dev/null | grep -q 200; then
      echo "      ✓ 后端就绪"
      return 0
    fi
    sleep 2
  done
  echo "      ✗ 后端超时未就绪，请查看 /tmp/mescs.log"
  return 1
}

stop_all() {
  echo "停止服务…"
  if pkill -f start_model 2>/dev/null; then echo "  已停模型"; else echo "  模型未运行"; fi
  if pkill -f "uvicorn backend.main:app" 2>/dev/null; then echo "  已停后端"; else echo "  后端未运行"; fi
}

status() {
  lsof -i :$MODEL_PORT >/dev/null 2>&1 && echo "模型(8001): 运行中" || echo "模型(8001): 已停止"
  lsof -i :$API_PORT >/dev/null 2>&1 && echo "后端(8000): 运行中" || echo "后端(8000): 已停止"
}

case "${1:-start}" in
  start)
    start_model
    wait_model
    start_api
    wait_api
    echo
    echo "=== 智能客服已启动（完全离线）==="
    echo "网页 Widget：用浏览器打开 frontend/widget.html（其 API_URL 指向 http://localhost:$API_PORT/api/chat）"
    echo "健康检查：  curl http://localhost:$API_PORT/"
    ;;
  stop) stop_all ;;
  restart) stop_all; sleep 2; "$0" start ;;
  status) status ;;
  *) echo "用法: $0 {start|stop|restart|status}"; exit 1 ;;
esac
