@echo off
title Eliminar Barrido Diario Programado
cd /d "%~dp0"
echo ================================================================
echo    ELIMINAR TAREA DE BARRIDO AUTOMATICO DE WINDOWS
echo ================================================================
echo.

set "TASK_NAME=BuscaInmuebles_BarridoDiario"

schtasks /delete /tn "%TASK_NAME%" /f

if %errorlevel% equ 0 (
    echo.
    echo [EXITO] La tarea programada '%TASK_NAME%' fue eliminada correctamente.
) else (
    echo.
    echo [AVISO] No se encontro la tarea o se requieren permisos de Administrador.
)

echo.
pause
