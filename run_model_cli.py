"""模型 CLI 包装器（macOS / WorkBuddy 沙箱专用）。

作用：用 `python -S` 跳过 WorkBuddy 注入的 sitecustomize 文件访问 broker，
手动把 .venv-sys 的 site-packages 加进 sys.path，再转发到 mlx_lm 的 CLI。

这样在「WorkBuddy 内置终端」和「自己 Mac 终端」都能直接跑模型，无需关心 broker。

用法（与 mlx_lm 原生命令一致，仅第一个参数是子命令）：
  .venv-sys/bin/python -S run_model_cli.py chat     --model mlx-community/Qwen2.5-3B-Instruct-4bit
  .venv-sys/bin/python -S run_model_cli.py generate --model mlx-community/Qwen2.5-3B-Instruct-4bit --prompt "你的问题"
  .venv-sys/bin/python -S run_model_cli.py server   --model mlx-community/Qwen2.5-3B-Instruct-4bit --port 8001
"""
import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_SP = os.path.join(_HERE, ".venv-sys", "lib", "python3.9", "site-packages")
if _SP not in sys.path:
    sys.path.insert(0, _SP)

_SUBCOMMANDS = {
    "chat": "mlx_lm.chat",
    "generate": "mlx_lm.generate",
    "server": "mlx_lm.server",
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in _SUBCOMMANDS:
        print("用法: python -S run_model_cli.py {chat|generate|server} [参数]")
        print("  chat     交互式对话（终端里直接跟模型聊）")
        print("  generate  单次生成: --model <id> --prompt \"...\"")
        print("  server    起 OpenAI 兼容服务: --model <id> --port 8001")
        print("示例:")
        print('  python -S run_model_cli.py chat --model mlx-community/Qwen2.5-3B-Instruct-4bit')
        sys.exit(1)

    sub = sys.argv[1]
    rest = sys.argv[2:]
    mod_name = _SUBCOMMANDS[sub]
    mod = __import__(mod_name, fromlist=["main"])
    # 让子命令自己的 argparse 收到正确参数（去掉我们的子命令名）
    sys.argv = [mod_name] + rest
    mod.main()


if __name__ == "__main__":
    main()
