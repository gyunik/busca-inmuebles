@echo off
TITLE Subir Busca Inmuebles a GitHub
cd /d "%~dp0"

echo ========================================================
echo       SUBIR PROYECTO A GITHUB PARA RENDER.COM
echo ========================================================
echo.

if not exist ".git" (
    echo [1/4] Inicializando repositorio Git...
    git init
    git branch -M main
) else (
    echo [1/4] Repositorio Git ya existe.
)

echo [2/4] Agregando archivos del proyecto...
git add .

echo [3/4] Creando version (commit)...
git commit -m "Publicar Busca Inmuebles en Render"

echo.
echo ========================================================
echo   PASO FINAL: Vincular con tu repositorio de GitHub
echo ========================================================
echo   1. Entra a https://github.com/new
echo   2. Crea un repositorio (ejemplo: busca-inmuebles)
echo   3. Copia el enlace HTTPS (ej: https://github.com/tu-usuario/busca-inmuebles.git)
echo ========================================================
echo.

set /p REPO_URL="Pega aqui el enlace de tu repositorio de GitHub: "

if "%REPO_URL%"=="" (
    echo [AVISO] No ingresaste enlace. Puedes vincularlo luego con:
    echo git remote add origin TU_URL
    echo git push -u origin main
    pause
    exit /b
)

git remote remove origin >nul 2>&1
git remote add origin %REPO_URL%

echo.
echo [4/4] Subiendo archivos a GitHub...
git push -u origin main

echo.
echo ========================================================
echo   LISTO! Archivos subidos exitosamente a GitHub.
echo   Ahora puedes ir a Render.com y conectar tu repositorio.
echo ========================================================
pause
