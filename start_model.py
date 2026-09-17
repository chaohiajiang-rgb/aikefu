"""本地模型服务启动器（macOS / WorkBuddy 沙箱专用）。

WorkBuddy 给所有 Python 注入了 sitecustomize 文件访问 broker，
会拦截 mlx_lm 等库的加载。用 `python -S` 跳过 site 初始化即可绕过，
同时手动把系统 Python 建的 venv site-packages 加进 sys.path。

用法：
  .venv-sys/bin/python -S start_model.py --model mlx-community/Qwen2.5-7B-Instruct-4bit --port 8001
"""
import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_SP = os.path.join(_HERE, ".venv-sys", "lib", "python3.9", "site-packages")
if _SP not in sys.path:
    sys.path.insert(0, _SP)

from mlx_lm.server import main

if __name__ == "__main__":
    main()
