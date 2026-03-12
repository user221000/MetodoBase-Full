@echo off
REM ============================================================
REM  METODO BASE - BUILD COMPLETO
REM  Consultoria Hernandez
REM  Genera ejecutable + instalador desde cero
REM ============================================================

echo ============================================================
echo  METODO BASE - BUILD COMPLETO
echo  Consultoria Hernandez
echo ============================================================
echo.

REM Usar Python del entorno virtual si existe
set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

REM Paso 1: Limpiar TODOS los artefactos anteriores
echo [1/5] Limpiando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist Output rmdir /s /q Output
if exist MetodoBase.spec del /f /q MetodoBase.spec
echo     build\   eliminado
echo     dist\    eliminado
echo     Output\  eliminado
echo     .spec    eliminado
echo OK
echo.

REM Paso 2: Ejecutar tests
echo [2/5] Ejecutando tests...
"%PYTHON_EXE%" -m pytest tests/ -v --tb=short
if errorlevel 1 (
    echo.
    echo ERROR: Los tests fallaron. Corrige los errores antes de compilar.
    pause
    exit /b 1
)
echo OK
echo.

REM Paso 3: Empaquetar con PyInstaller (via setup.py)
echo [3/5] Empaquetando con PyInstaller...
"%PYTHON_EXE%" setup.py build
if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller fallo.
    pause
    exit /b 1
)
echo OK
echo.

REM Paso 4: Crear instalador con Inno Setup
echo [4/5] Creando instalador con Inno Setup...
set "ISCC_EXE="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"                           set "ISCC_EXE=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe"                                 set "ISCC_EXE=C:\Program Files\Inno Setup 6\ISCC.exe"
if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Inno Setup 6\ISCC.exe"       set "ISCC_EXE=C:\Users\%USERNAME%\AppData\Local\Programs\Inno Setup 6\ISCC.exe"

if "%ISCC_EXE%"=="" (
    echo.
    echo ERROR: Inno Setup 6 no encontrado. Instalalo desde https://jrsoftware.org/isinfo.php
    pause
    exit /b 1
)

"%ISCC_EXE%" setup_installer.iss
if errorlevel 1 (
    echo.
    echo ERROR: Inno Setup fallo.
    pause
    exit /b 1
)
echo OK
echo.

REM Paso 5: Resumen
echo [5/5] Build completado exitosamente!
echo.
echo ============================================================
echo  ARCHIVOS GENERADOS:
echo ============================================================
echo.
echo   Ejecutable : dist\MetodoBase\MetodoBase.exe
echo   Instalador : Output\MetodoBaseSetup_v1.0.0.exe
echo.
echo ============================================================
echo  PROXIMOS PASOS:
echo ============================================================
echo.
echo   1. Prueba el ejecutable en otra PC sin Python
echo   2. Prueba el instalador completo
echo   3. Distribuye a los gimnasios
echo.
pause
