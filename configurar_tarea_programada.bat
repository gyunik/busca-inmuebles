@echo off
title Configurar Barrido Diario Programado
cd /d "%~dp0"
echo ================================================================
echo    CONFIGURADOR DE BARRIDOS MASIVOS AUTOMATICOS EN WINDOWS
echo ================================================================
echo.
echo Este script creara una tarea automatica en el Programador de Tareas
echo de Windows para actualizar todos los portales diariamente a las 04:00 AM
echo de forma 100%% silenciosa en segundo plano.
echo.

set "VBS_PATH=%~dp0ejecutar_barrido_silencioso.vbs"
set "TASK_NAME=BuscaInmuebles_BarridoDiario"

schtasks /create /tn "%TASK_NAME%" /tr "wscript.exe \"%VBS_PATH%\"" /sc daily /st 04:00 /f

if %errorlevel% equ 0 (
    echo.
    echo ================================================================
    echo [EXITO] La tarea programada '%TASK_NAME%' fue creada con exito!
    echo Se ejecutara todos los dias a las 04:00 AM automaticamente.
    echo Los resultados quedaran registrados en:
    echo   backend\data\barrido_log.txt
    echo ================================================================
) else (
    echo.
    echo [AVISO] Se requieren permisos de Administrador para registrar la tarea.
    echo Haz clic derecho sobre este archivo y selecciona 'Ejecutar como Administrador'.
)

echo.
pause
