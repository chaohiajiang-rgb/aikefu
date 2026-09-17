@echo off
REM ============================================================
REM  MES 智能客服 - 用 NSSM 注册为 Windows 服务（离线本地模型版）
REM  前置：
REM    1) 已用 ollama_setup.bat 或 vLLM 起好本地模型，监听本地 OpenAI 兼容端点
REM    2) 已将 mes-ai-cs/ 整个目录拷到内网服务器（如 D:\mes-ai-cs\）
REM    3) 已建好 venv 并 pip install -r requirements.txt
REM    4) 已将 .env.offline 复制为 D:\mes-ai-cs\.env
REM  用法：右键“以管理员身份运行”本脚本
REM  说明：端口用 8000，避开现有 MESApi 的 3000
REM ============================================================
setlocal
set APP_NAME=MESChat
set INSTALL_DIR=D:\mes-ai-cs
set PYTHON_EXE=%INSTALL_DIR%\.venv\Scripts\python.exe

REM 若服务已存在先移除，避免重复注册报错
nssm stop %APP_NAME% >nul 2>&1
nssm remove %APP_NAME% confirm >nul 2>&1

nssm install %APP_NAME% "%PYTHON_EXE%"
nssm set %APP_NAME% AppParameters "-m uvicorn backend.main:app --host 0.0.0.0 --port 8000"
nssm set %APP_NAME% AppDirectory "%INSTALL_DIR%"
nssm set %APP_NAME% DisplayName "MES 智能客服"
nssm set %APP_NAME% Description "FastAPI + 本地离线模型客服"
nssm set %APP_NAME% Start SERVICE_AUTO_START
nssm set %APP_NAME% AppExit Default Restart

nssm start %APP_NAME%
if errorlevel 1 (
    echo [错误] 服务启动失败，请用 nssm status %APP_NAME% 排查，并确认本地模型端点可达
    pause
    exit /b 1
)
echo.
echo [OK] 服务 %APP_NAME% 已启动
echo      健康检查: http://localhost:8000/
echo      网页 Widget 的 API_URL 需指向 http://<内网IP>:8000/api/chat
pause
