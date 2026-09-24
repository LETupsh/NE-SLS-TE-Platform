@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".streamlit\secrets.toml" (
    echo [错误] 缺少登录配置：.streamlit\secrets.toml 不存在。
    echo 请先复制模板并填入账号密码：
    echo     copy .streamlit\secrets.toml.example .streamlit\secrets.toml
    pause
    exit /b 1
)

echo 启动风光储一体化综合分析平台 (NE-SLS-TE-Platform)...
streamlit run integrated_app.py
pause
