"""MES 智能客服后端：FastAPI 服务。

接口：
  GET  /           健康检查
  POST /api/chat   {"session_id": "...", "message": "..."} -> {"reply": "..."}

多轮对话：服务端按 session_id 在内存中维护历史（生产建议换 redis）。
知识检索：每次提问先用 rag 召回相关片段，拼进 system prompt 作为「知识片段」。
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from . import ai_client, config, rag

app = FastAPI(title="MES 智能客服", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# session_id -> 历史消息列表
_sessions: dict[str, list[dict]] = {}


class ChatReq(BaseModel):
    session_id: str = "default"
    message: str


def _build_messages(session_id: str, user_msg: str) -> list[dict]:
    history = _sessions.get(session_id, [])

    # 1) 拼接知识片段
    hits = rag.retriever.retrieve(user_msg)
    if hits:
        knowledge = "【知识片段】\n" + "\n---\n".join(hits)
        system_content = config.SYSTEM_PROMPT + "\n\n" + knowledge
    else:
        system_content = config.SYSTEM_PROMPT

    messages = [{"role": "system", "content": system_content}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_msg})
    return messages


def _push_history(session_id: str, user_msg: str, reply: str) -> None:
    hist = _sessions.setdefault(session_id, [])
    hist.append({"role": "user", "content": user_msg})
    hist.append({"role": "assistant", "content": reply})
    # 仅保留最近 MAX_HISTORY 轮
    keep = config.MAX_HISTORY * 2
    if len(hist) > keep:
        _sessions[session_id] = hist[-keep:]


@app.get("/")
def health():
    return {
        "status": "ok",
        "model": config.AIHUB_MODEL,
        "knowledge_chunks": len(rag.retriever.chunks),
    }


@app.post("/api/chat")
async def chat(req: ChatReq):
    if not req.message.strip():
        return JSONResponse({"reply": "请输入您的问题。"}, status_code=400)

    messages = _build_messages(req.session_id, req.message)
    try:
        reply = ai_client.chat(messages)
    except ai_client.NoApiKeyError as e:
        reply = (
            "⚠️ 后端尚未配置 aihub API Key。\n"
            "请在项目根目录 .env 中填写 AIHUB_API_KEY 后重启服务。\n"
            f"（当前提示：{e}）"
        )
        return JSONResponse({"reply": reply, "degraded": True})
    except Exception as e:  # noqa: BLE001
        reply = f"调用大模型失败：{e}"
        return JSONResponse({"reply": reply, "error": True}, status_code=502)

    _push_history(req.session_id, req.message, reply)
    return {"reply": reply}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
