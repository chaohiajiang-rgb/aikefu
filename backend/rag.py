"""轻量知识库检索（零额外依赖版本）。

先用「字符 bigram 重叠度」做召回，跑通 MVP 无需安装向量库。
后续要升级精度时，把 _retrieve 换成 chromadb / bge 向量检索即可，接口不变。

知识库来源：backend/knowledge 下的所有 .txt 文件，按空行分段切块。
"""
import os
import re

from . import config


def _bigrams(text: str) -> set:
    # 去掉空白，取字符级 bigram，作为中文友好的重叠特征
    t = re.sub(r"\s+", "", text)
    return {t[i : i + 2] for i in range(len(t) - 1)}


def _split_chunks(text: str, max_len: int = 240) -> list[str]:
    # 按空行分段，超长段落再按标点切到 max_len 以内
    raw = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    for p in raw:
        if len(p) <= max_len:
            chunks.append(p)
            continue
        buf = ""
        for sent in re.split(r"(?<=[。；;])", p):
            if len(buf) + len(sent) > max_len and buf:
                chunks.append(buf.strip())
                buf = sent
            else:
                buf += sent
        if buf.strip():
            chunks.append(buf.strip())
    return chunks


class Retriever:
    def __init__(self, knowledge_dir: str = config.KNOWLEDGE_DIR):
        self.chunks: list[str] = []
        self._index: list[set] = []
        self._load(knowledge_dir)

    def _load(self, knowledge_dir: str) -> None:
        if not os.path.isdir(knowledge_dir):
            return
        for fn in sorted(os.listdir(knowledge_dir)):
            if not fn.endswith(".txt"):
                continue
            with open(os.path.join(knowledge_dir, fn), "r", encoding="utf-8") as f:
                for c in _split_chunks(f.read()):
                    self.chunks.append(c)
                    self._index.append(_bigrams(c))

    def retrieve(self, query: str, top_k: int = config.RETRIEVE_TOP_K) -> list[str]:
        if not self.chunks:
            return []
        q = _bigrams(query)
        if not q:
            return []
        scored = []
        for i, idx in enumerate(self._index):
            inter = len(q & idx)
            if inter == 0:
                continue
            union = len(q | idx)
            scored.append((inter / union, i))
        scored.sort(reverse=True)
        return [self.chunks[i] for _, i in scored[:top_k]]


# 单例，服务启动时加载一次
retriever = Retriever()
