@echo off
REM ============================================================
REM  MES 智能客服 · 内网一键部署（Windows 服务版）
REM ------------------------------------------------------------
REM  前置（一次性，仅需第一次）：
REM    1) 安装 Python 3.10+ 并勾选 "Add to PATH"
REM    2) 运行同目录 ollama_setup.bat 装好 Ollama 并拉取本地模型
REM       （如 qwen2.5:14b / glm4:9b / deepseek-r1:14b-distill）
REM    3) 把 nssm.exe 放到本目录（deploy\）或确保 nssm 在 PATH
REM
REM  用法：把整个 mes-ai-cs 目录拷到内网服务器（如 D:\mes-ai-cs\），
REM        右键 deploy\deploy_intranet.bat “以管理员身份运行”。
REM
REM  本脚本会自动完成：建 venv → 装依赖 → 生成 .env → NSSM 注册并启动。
REM  端口固定 8000，避开现有 MESApi 的 3000。
REM ============================================================
setlocal enabledelayedexpansion
set APP_NAME=MESChat

REM 规范化 INSTALL_DIR = deploy 的上一级（即 mes-ai-cs 根）
for %%I in ("%~dp0..") do set INSTALL_DIR=%%~fI
set VENV=%INSTALL_DIR%\.venv
set PY=%VENV%\Scripts\python.exe
set PIP=%VENV%\Scripts\pip.exe
set NSSM=%~dp0nssm.exe
if not exist "%NSSM%" set NSSM=nssm

echo ============================================================
echo  MES 智能客服 内网一键部署
echo  安装目录: %INSTALL_DIR%
echo ============================================================

REM 0) 依赖检查
where python >nul 2>&1 || (echo [错误] 未找到 python，请先安装 Python 3.10+ 并勾选 Add to PATH & pause & exit /b 1)
where %NSSM% >nul 2>&1 || (echo [错误] 未找到 nssm（deploy\nssm.exe 或 PATH），请放入 deploy\ 目录 & pause & exit /b 1)

REM 1) 建虚拟环境
if not exist "%PY%" (
  echo [1/5] 创建虚拟环境 .venv ...
  python -m venv "%VENV%"
  if errorlevel 1 (echo [错误] 创建 venv 失败 & pause & exit /b 1)
) else (
  echo [1/5] 虚拟环境已存在，跳过
)

REM 2) 装依赖（优先离线 wheels，回退在线）
echo [2/5] 安装后端依赖 ...
if exist "%~dp0wheels" (
  "%PIP%" install --no-index --find-links "%~dp0wheels" -r "%INSTALL_DIR%\requirements-server.txt" || "%PIP%" install -r "%INSTALL_DIR%\requirements-server.txt"
) else (
  "%PIP%" install -r "%INSTALL_DIR%\requirements-server.txt"
)
if errorlevel 1 (echo [错误] 依赖安装失败，请检查网络或放置离线 wheels & pause & exit /b 1)

REM 3) 生成 .env（缺失才用离线模板，避免覆盖已有配置）
if not exist "%INSTALL_DIR%\.env" (
  echo [3/5] 生成 .env（离线本地模型模板）...
  copy "%~dp0.env.offline" "%INSTALL_DIR%\.env" >nul
) else (
  echo [3/5] .env 已存在，保留不动
)

REM 4) NSSM 注册
echo [4/5] 注册 Windows 服务 %APP_NAME% ...
%NSSM% stop %APP_NAME% >nul 2>&1
%NSSM% remove %APP_NAME% confirm >nul 2>&1
%NSSM% install %APP_NAME% "%PY%"
%NSSM% set %APP_NAME% AppParameters "-m uvicorn backend.main:app --host 0.0.0.0 --port 8000"
%NSSM% set %APP_NAME% AppDirectory "%INSTALL_DIR%"
%NSSM% set %APP_NAME% DisplayName "MES 智能客服"
%NSSM% set %APP_NAME% Description "FastAPI + 本地离线模型客服"
%NSSM% set %APP_NAME% Start SERVICE_AUTO_START
%NSSM% set %APP_NAME% AppExit Default Restart

REM 5) 启动 + 健康检查
echo [5/5] 启动服务 ...
%NSSM% start %APP_NAME%
timeout /t 3 >nul
echo.
echo 健康检查:
curl -s http://localhost:8000/ || echo (服务启动中，稍后访问 http://localhost:8000/ 确认)
echo.
echo ============================================================
echo [完成] 服务 %APP_NAME% 已注册并设为开机自启。
echo.
echo 下一步：让 UTGMES 网页指向本服务 ——
echo   编辑 UTGMES/UTGME_Sserver/web/index.html，把
echo     ^<meta name="mes-ai-cs-api" content="http://127.0.0.1:8000/api/chat"^>
echo   的 content 改成 http://^<本机内网IP^>:8000/api/chat
echo   （若 AI 后端与 UTGMES 同机，直接用 http://127.0.0.1:8000/api/chat）
echo ============================================================
pause
