# MES 智能客服（MVP 骨架）

工厂内部 MES / 产线问答智能客服。后端 FastAPI 调 aihub 大模型网关（GLM/DeepSeek），
内置轻量 RAG 检索（无需先装向量库），前端为单文件网页聊天 Widget，另附 customtkinter 桌面调试端。

## 目录结构

```
mes-ai-cs/
├── backend/
│   ├── main.py          # FastAPI 服务（/api/chat 多轮 + 知识检索）
│   ├── ai_client.py     # aihub OpenAI 协议封装
│   ├── rag.py           # 轻量知识库检索（字符 bigram 重叠，零依赖）
│   ├── config.py        # 读 .env
│   └── knowledge/       # 知识库 .txt（按空行分段，可自行增删）
├── frontend/
│   └── widget.html      # 单文件网页客服 Widget（Tailwind+Alpine）
├── desktop_client.py    # customtkinter 桌面调试端
├── .env.example
└── requirements.txt
```

## 快速启动

```bash
# 1. 安装依赖（建议虚拟环境）
pip install -r requirements.txt

# 2. 配置 Key
cp .env.example .env
# 编辑 .env，填入 AIHUB_API_KEY（注意 I/l 易混淆字符，直接粘贴原文）

# 3. 启动后端（端口 8000）
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 4. 验证
curl http://localhost:8000/            # 健康检查，返回知识块数量
curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"t1","message":"Tray 和 Ink 怎么绑定？"}'
```

## 三种使用方式

1. **网页 Widget**：用浏览器打开 `frontend/widget.html`，右下角即客服入口；
   生产嵌入时把 `widget.html` 里 `<div x-data="csWidget()">` 整段拷进你的页面，
   并将 `API_URL` 改为同域 `/api/chat` 或后端地址。
2. **桌面调试端**：`python desktop_client.py`（需先启动后端）。
3. **开放 API**：任何系统 POST `/api/chat` 即可集成。

## 升级 RAG 精度（可选）

当前用字符 bigram 做召回，适合小知识库。知识量上来后，把 `backend/rag.py` 的
`Retriever.retrieve` 换成 chromadb / bge 向量检索，接口不变：

```bash
pip install chromadb
```

保留 `knowledge/` 下的 .txt，改为 embedding 入库，再在 `retrieve` 里做向量 top-k 查询。

## 部署说明

- 后端可随 MES 服务一起部署到内网 Windows 服务器（NSSM 注册 / pkg 打包思路同现有 MESApi）。
- 知识库维护：直接编辑 `backend/knowledge/*.txt`，重启后端即生效（后续可接 Navicat / api_summary 表统一管理）。
- 多轮历史当前存内存，生产建议换 redis 并按 session 过期清理。
