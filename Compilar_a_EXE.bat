@echo off
title Compilar Clipboard Sync a EXE
echo ============================================================
echo   Compilando Clipboard Sync a archivo ejecutable (.exe)
echo ============================================================
echo.
echo Este proceso puede tardar unos minutos...
echo.

python build_exe.py

echo.
echo Presiona cualquier tecla para salir...
pause >nul
