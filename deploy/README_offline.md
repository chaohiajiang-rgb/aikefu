# 智能客服 - 内网离线部署指南

适用场景：**内网无法访问 aihub 网关，或要求完全网络隔离**。
用本地开源模型（Ollama / vLLM）替代 glm-5.2，后端代码零改动（OpenAI 协议天然兼容）。

## 整体架构

```
工厂内网用户 ──网页 Widget──> FastAPI 后端(8000) ──> 本地模型端点(11434/8001)
                         │
                         └─> RAG 知识库(backend/knowledge/*.txt)
```

后端与大模型之间只走内网 HTTP，无任何外网依赖。

## 步骤一：起本地模型（二选一）

### A. Ollama（最简单，CPU/GPU 均可）
1. 到 https://ollama.com/download 安装 Ollama for Windows（默认开机自启，监听 11434）
2. 拉模型（按显存选）：
   - `ollama pull qwen2.5:14b` （推荐）
   - `ollama pull glm4:9b`
   - `ollama pull deepseek-r1:14b-distill`
3. 验证：`curl http://localhost:11434/v1/models`

### B. vLLM（GPU 服务器，高并发）
```bash
pip install vllm
python -m vllm.entrypoints.openai.api_server ^
  --model Qwen/Qwen2.5-14B-Instruct --host 0.0.0.0 --port 8001
```
> 注意：vLLM 用 8001，避免和后端 8000 冲突。

## 步骤二：配置后端

1. 把 `mes-ai-cs/` 整个目录拷到内网服务器（如 `D:\mes-ai-cs\`）
2. 建 venv 装依赖：
   ```
   D:\mes-ai-cs\.venv\Scripts\python.exe -m venv D:\mes-ai-cs\.venv
   D:\mes-ai-cs\.venv\Scripts\pip.exe install -r D:\mes-ai-cs\requirements.txt
   ```
3. 复制离线配置：把 `deploy\.env.offline` 复制为 `D:\mes-ai-cs\.env`，
   确认 `AIHUB_BASE_URL` / `AIHUB_MODEL` 与实际模型端点、模型名一致。

## 步骤三：一键注册为服务（推荐）

以管理员身份运行 `deploy\deploy_intranet.bat`，脚本会自动完成：
建 venv → 装后端依赖（requirements-server.txt）→ 生成 .env（离线模板）→
NSSM 注册并启动 Windows 服务 `MESChat`（端口 8000，开机自启）。

前置（仅首次）：装好 Python 3.10+（勾 Add to PATH）、运行 `ollama_setup.bat`
装好 Ollama 并拉取模型、把 `nssm.exe` 放到 `deploy\`。

常用命令：
```
nssm status MESChat
nssm stop MESChat
nssm start MESChat
```

> 旧版 `nssm_install.bat` 仍保留：它假设 venv 与 .env 已手动建好，
> 仅做「注册+启动」，适合二次调试。新部署直接用 `deploy_intranet.bat`。

## 步骤四：前端 Widget 指向内网（已集成进 UTGMES）

智能客服 Widget 已嵌入 UTGMES 网页版（`web/cs_widget.js`），无需改任何 JS。
只需改 `UTGMES/UTGME_Sserver/web/index.html` 顶部这个 meta 即可切换后端地址：

```html
<meta name="mes-ai-cs-api" content="http://127.0.0.1:8000/api/chat">
```

- ⚠️ **重点：`127.0.0.1` 只对「打开网页的那台电脑自己」生效。** Widget 的 fetch
  是在每个用户的浏览器里发出的：meta 写 `127.0.0.1` 时，只有「AI 后端与 UTGMES
  装在同一台服务器、且用户通过该服务器本机浏览器访问」时才通。只要用户是从
  自己工位电脑打开 UTGMES 网页，meta 就必须写 **AI 后端所在机器的内网 IP**：
  `http://<AI后端内网IP>:8000/api/chat`（同机部署同理，写该机的内网 IP，
  不要写 127.0.0.1）。
- 改完刷新 UTGMES 页面，左侧栏「🤖 智能客服」与右下浮动按钮即可对话。

（早期独立版 `frontend/widget.html` 的 `API_URL` 写法已废弃，统一改用上述 meta。）

## 步骤五：知识库随包维护

拷 `backend/knowledge/*.txt` 到服务器；改完重启服务（`net stop/start MESChat` 或 `nssm restart MESChat`）即生效。
知识量大时把 `rag.py` 换成 chromadb 向量检索（接口不变）。

## 注意事项
- **端口**：用 8000，避开现有 MESApi 的 3000。
- **防火墙**：部署后如工位电脑访问不了 `http://<服务器IP>:8000/`，在服务器
  Windows 防火墙放行 8000 入站（`netsh advfirewall firewall add rule name="MESChat" dir=in action=allow protocol=TCP localport=8000`）。
- **离线依赖**：`deploy\wheels\` 已备好 py3.12/3.13 的 Windows wheels
  （fastapi 0.141.1 / uvicorn 0.53.0 / openai 3.14.1 / python-dotenv 1.1.0，
  与 Mac 上验证通过的版本一致），`deploy_intranet.bat` 会自动优先离线安装。
- **模型能力差异**：开源模型（qwen2.5/glm4）取代 glm-5.2，复杂推理略弱，工艺问题建议配合更全的知识库。
- **显存**：14B 模型建议 ≥16GB 显存；无 GPU 可量化后 CPU 跑（速度慢）。
- **CORS**：后端已 `allow_origins=["*"]`，内网跨域访问无碍。
- **健康检查**：`http://localhost:8000/` 返回 `knowledge_chunks` 数量即正常。
