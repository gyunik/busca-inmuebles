@echo off
title BuscaInmuebles - Acceso Web Publico (HTTPS)
cd /d "%~dp0"

set "PY_CMD=python"
where python >nul 2>&1
if errorlevel 1 (
    where py >nul 2>&1
    if not errorlevel 1 (
        set "PY_CMD=py"
    ) else if exist "C:\Users\gpy20\AppData\Local\Python\pythoncore-3.14-64\python.exe" (
        set "PY_CMD=C:\Users\gpy20\AppData\Local\Python\pythoncore-3.14-64\python.exe"
    )
)

"%PY_CMD%" lanzar_acceso_web.py
pause
