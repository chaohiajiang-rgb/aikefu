@echo off
REM ============================================================
REM  本地模型离线部署 - Ollama 版（最简单，CPU/GPU 均可）
REM  替代说明：aihub 的 glm-5.2 权重不公开，离线环境用开源模型顶替：
REM    qwen2.5:14b   （推荐，中文强，14B 需约 9GB 显存或量化后 CPU 可跑）
REM    glm4:9b       （智谱开源 9B，中文友好）
REM    deepseek-r1:14b-distill （推理型，适合多步工艺问题）
REM  Ollama 提供 /v1 OpenAI 兼容接口，后端无需改代码
REM ============================================================
echo [1/3] 请先到 https://ollama.com/download 安装 Ollama for Windows
echo        安装完成后 Ollama 默认开机自启并监听 http://localhost:11434
pause

echo [2/3] 拉取模型（按机器显存选一个，下面默认 qwen2.5:14b）
ollama pull qwen2.5:14b
REM 备选：ollama pull glm4:9b
REM 备选：ollama pull deepseek-r1:14b-distill

echo [3/3] 确认本地推理端点可用
curl -s http://localhost:11434/v1/models
echo.
echo [完成] 本地模型就绪。请将 deploy\.env.offline 复制为上级目录的 .env，
echo         并把 AIHUB_MODEL 改成你实际拉取的模型名，再运行 nssm_install.bat
pause
