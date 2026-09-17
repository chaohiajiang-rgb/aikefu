"""aihub 大模型调用封装（OpenAI 协议）。

aihub 网关同时兼容 OpenAI 协议：
  POST {AIHUB_BASE_URL}/chat/completions  Bearer 鉴权
可用模型：glm-5.2 / glm-5.3 / glm-5.3-flash / deepseek-v4-pro / deepseek-v4-flash ...
glm 系列为推理模型，会额外返回 reasoning_content，但标准 content 字段始终可用。
"""
from openai import OpenAI

from . import config


class NoApiKeyError(RuntimeError):
    """未配置 AIHUB_API_KEY 时抛出。"""


def chat(messages: list[dict], temperature: float = 0.3) -> str:
    """调用大模型，返回助手回复文本。

    messages 形如 [{"role": "system", ...}, {"role": "user", ...}, ...]
    """
    if not config.AIHUB_API_KEY:
        raise NoApiKeyError("AIHUB_API_KEY 未配置，请在 .env 中填写后重启服务")

    client = OpenAI(base_url=config.AIHUB_BASE_URL, api_key=config.AIHUB_API_KEY)
    resp = client.chat.completions.create(
        model=config.AIHUB_MODEL,
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content or ""
