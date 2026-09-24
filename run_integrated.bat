@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 启动风光储一体化综合分析平台 (NE-SLS-TE-Platform)...
streamlit run integrated_app.py
pause
