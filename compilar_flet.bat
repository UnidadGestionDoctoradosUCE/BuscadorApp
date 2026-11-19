@echo off
echo Compilando AppBuscador con interfaz moderna Flet...
flet pack main.py --name "AppBuscador" --icon "imagenes\logouce.png" --add-data "imagenes;imagenes" --add-data "data;data" -y
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Fallo la compilacion. Verifica que flet y pyinstaller esten instalados.
    pause
    exit /b 1
)
del /q generated-*.ico 2>nul
if exist build rmdir /s /q build
if exist AppBuscador.spec del /q AppBuscador.spec
echo.
echo [OK] Ejecutable generado en la carpeta dist\AppBuscador.exe
pause
