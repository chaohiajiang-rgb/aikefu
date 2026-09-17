"""MES 智能客服 — 桌面调试客户端（customtkinter 深色工业风）。

本地调试用：调用后端 /api/chat，验证问答链路与知识检索效果。
运行：先启动后端（uvicorn backend.main:app --port 8000），再 python desktop_client.py
依赖：pip install customtkinter requests
"""
import threading
import tkinter
import uuid

import customtkinter as ctk
import requests

API_URL = "http://localhost:8000/api/chat"
SESSION_ID = "desktop-" + uuid.uuid4().hex[:8]

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class ChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MES 智能客服 · 调试端")
        self.geometry("460x640")

        # 头部
        header = ctk.CTkLabel(
            self, text="MES 产线智能客服", font=ctk.CTkFont(size=16, weight="bold")
        )
        header.pack(pady=(12, 6))

        # 消息区
        self.body = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.body.pack(fill="both", expand=True, padx=12, pady=6)

        self._bot("你好，我是 MES 产线智能客服。可以问我追溯、工单、Tray/Ink 绑定等问题。")

        # 输入区
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=12, pady=(0, 12))

        self.entry = ctk.CTkEntry(bottom, placeholder_text="输入 MES / 产线问题…")
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry.bind("<Return>", lambda e: self.send())

        self.send_btn = ctk.CTkButton(bottom, text="发送", width=72, command=self.send)
        self.send_btn.pack(side="right")

    def _bubble(self, text: str, is_user: bool):
        align = "e" if is_user else "w"
        color = ("#1d9e75", "#0f6e56") if is_user else ("#2b3242", "#2b3242")
        frame = ctk.CTkFrame(self.body, fg_color=color, corner_radius=10)
        frame.pack(anchor=align, pady=3, padx=2, fill="x")
        ctk.CTkLabel(
            frame, text=text, wraplength=360, justify="left",
            font=ctk.CTkFont(size=13),
        ).pack(padx=10, pady=6)

    def _user(self, text: str):
        self._bubble(text, True)

    def _bot(self, text: str):
        self._bubble(text, False)
        self.body._parent_canvas.yview_moveto(1.0)

    def send(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, "end")
        self._user(text)

        def worker():
            self.send_btn.configure(state="disabled")
            try:
                resp = requests.post(
                    API_URL,
                    json={"session_id": SESSION_ID, "message": text},
                    timeout=60,
                )
                data = resp.json()
                reply = data.get("reply", "（无回复）")
            except Exception as e:  # noqa: BLE001
                reply = f"连接后端失败：{e}"
            self._bot(reply)
            self.send_btn.configure(state="normal")

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    ChatApp().mainloop()
