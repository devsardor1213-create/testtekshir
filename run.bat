@echo off
echo ==============================================
echo Tizim ishga tushirilmoqda...
echo ==============================================
echo.

start http://127.0.0.1:8000/index.html
python -m uvicorn main:app --reload

pause
