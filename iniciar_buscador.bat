@echo off
TITLE Busca Inmuebles - Agregador Multicanal CABA y GBA
cd /d "%~dp0"

echo ========================================================
echo   INICIANDO BUSCADOR DE INMUEBLES
echo   Mercado Libre | Zonaprop | Argenprop | Mudafy
echo ========================================================
echo.

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

echo Iniciando servidor en http://localhost:8000 ...
start "BuscaInmuebles Server" "%PY_CMD%" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

timeout /t 3 /nobreak >nul
start http://127.0.0.1:8000

echo.
echo Aplicacion iniciada correctamente en http://localhost:8000
echo Puedes cerrar esta ventana o dejarla minimizada.
pause
