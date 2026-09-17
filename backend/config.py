"""配置加载：从 .env 读取 aihub 网关与大模型参数。"""
import os
from dotenv import load_dotenv

# 加载项目根目录下的 .env（backend 目录的上一级）
_BASE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_BASE)
load_dotenv(os.path.join(_ROOT, ".env"))


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default)


# aihub 大模型网关（OpenAI 协议）
AIHUB_BASE_URL = _get("AIHUB_BASE_URL", "https://aihub.bielcrystal.com/v1")
AIHUB_API_KEY = _get("AIHUB_API_KEY", "")
AIHUB_MODEL = _get("AIHUB_MODEL", "glm-5.2")

# 客服系统提示词（MES 产线领域专家人设）
SYSTEM_PROMPT = _get(
    "SYSTEM_PROMPT",
    "你是伯恩光学（BYD/Bern）MES 产线智能客服助手，服务于工厂内部的工艺、设备、"
    "追溯与工单问题。回答必须基于提供的「知识片段」，用简洁中文、分点说明；"
    "若知识片段未覆盖，请如实说明无法确认并建议联系对应工程师，不要编造数据。"
    "涉及 TrayID / InkID / PEcode 三级绑定、sn_trace 追溯链、AOI/手动分类时务必准确。",
)

# 知识库目录（backend/knowledge 下的 .txt 文件）
KNOWLEDGE_DIR = os.path.join(_BASE, "knowledge")

# 多轮对话保留的最大历史轮数
MAX_HISTORY = int(_get("MAX_HISTORY", "10"))

# 检索返回的知识片段数量
RETRIEVE_TOP_K = int(_get("RETRIEVE_TOP_K", "3"))
