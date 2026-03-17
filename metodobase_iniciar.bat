@echo off
:: ============================================================
::  MÉTODO BASE v2.0 — Script de inicio (modo portable)
::  Úsalo si el instalador no está disponible.
:: ============================================================
title Método Base - Iniciando...
setlocal

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"
set "PYTHON_EXE="

:: ── 1. Buscar Python ─────────────────────────────────────────
echo.
echo  ==========================================================
echo    METODO BASE v2.0
echo    Sistema de Planes Nutricionales para Gimnasios
echo  ==========================================================
echo.

:: Detectar Python en venv local primero
if exist "%VENV_DIR%\Scripts\python.exe" (
    set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
    echo  [OK] Usando entorno virtual en: %VENV_DIR%
    goto :check_deps
)

:: Python del sistema
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=python"
    echo  [OK] Usando Python del sistema
    goto :check_deps
)

python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=python3"
    echo  [OK] Usando Python3 del sistema
    goto :check_deps
)

:: Python no encontrado
echo.
echo  [ERROR] Python no encontrado en el sistema.
echo.
echo  Por favor instala Python 3.10 o superior desde:
echo    https://www.python.org/downloads/
echo.
echo  IMPORTANTE: Durante la instalacion, marca la opcion
echo    "Add Python to PATH"
echo.
pause
exit /b 1

:: ── 2. Crear/verificar entorno virtual y dependencias ────────
:check_deps
if exist "%VENV_DIR%\Scripts\activate.bat" goto :activate_venv

echo.
echo  Creando entorno virtual...
"%PYTHON_EXE%" -m venv "%VENV_DIR%"
if %errorlevel% neq 0 (
    echo  [ERROR] No se pudo crear el entorno virtual.
    pause
    exit /b 1
)

:activate_venv
call "%VENV_DIR%\Scripts\activate.bat"

:: Instalar dependencias si falta fastapi
python -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  Instalando dependencias (solo la primera vez)...
    echo  Esto puede tardar 2-5 minutos...
    echo.
    pip install -r "%SCRIPT_DIR%requirements.txt" -r "%SCRIPT_DIR%requirements_api.txt" --quiet
    if %errorlevel% neq 0 (
        echo  [ERROR] Error al instalar dependencias.
        echo  Revisa tu conexion a internet e intenta de nuevo.
        pause
        exit /b 1
    )
    echo  [OK] Dependencias instaladas correctamente.
)

:: ── 3. Iniciar servidor ───────────────────────────────────────
echo.
echo  Iniciando servidor MetodoBase...
echo.
echo  El navegador se abrira automaticamente en:
echo    http://localhost:8000
echo.
echo  *** NO CIERRES ESTA VENTANA ***
echo  Para detener el servidor presiona Ctrl+C
echo.
echo  ----------------------------------------------------------

cd /d "%SCRIPT_DIR%"
python api_server.py

echo.
echo  Servidor detenido.
pause
