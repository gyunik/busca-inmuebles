@echo off
TITLE Busca Inmuebles - Agregador Multicanal CABA y GBA
echo ========================================================
echo   INICIANDO BUSCADOR DE INMUEBLES MULTICANAL
echo   Mercado Libre ^| Zonaprop ^| Argenprop ^| Properati
echo ========================================================
echo.

echo Iniciando servidor y base de datos local...
start "BuscaInmuebles Server" cmd /c "cd /d %~dp0 && python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak >nul

echo Abriendo aplicacion en el navegador...
start http://127.0.0.1:8000

echo.
echo ========================================================
echo   Aplicacion lista y funcionando en:
echo   -> http://127.0.0.1:8000
echo   -> Documentacion API: http://127.0.0.1:8000/docs
echo.
echo   Para cerrar la app, simplemente cerra esta ventana
echo   o la ventana de consola del servidor.
echo ========================================================
echo.
pause
