@echo off
cd /d "%~dp0"
echo ===================================================
echo [%date% %time%] INICIANDO BARRIDO PROGRAMADO
echo ===================================================
python actualizar_base_de_datos.py >> "%~dp0backend\data\barrido_log.txt" 2>&1
echo [%date% %time%] BARRIDO PROGRAMADO FINALIZADO >> "%~dp0backend\data\barrido_log.txt"
