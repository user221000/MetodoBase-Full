@echo off
REM Script completo de build para Método Base
REM Ejecuta todos los pasos necesarios para crear el instalador final

echo ============================================================
echo METODO BASE - BUILD COMPLETO
echo Consultoria Hernandez
echo ============================================================
echo.

REM Paso 1: Limpiar builds anteriores
echo [1/5] Limpiando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist Output rmdir /s /q Output
echo OK

REM Paso 2: Ejecutar tests
echo.
echo [2/5] Ejecutando tests...
python -m pytest tests/ -v --tb=short
if errorlevel 1 (
    echo ERROR: Tests fallaron. Corrige los errores antes de compilar.
    pause
    exit /b 1
)
echo OK

REM Paso 3: Empaquetar con PyInstaller
echo.
echo [3/5] Empaquetando con PyInstaller...
python setup.py build
if errorlevel 1 (
    echo ERROR: PyInstaller fallo
    pause
    exit /b 1
)
echo OK

REM Paso 4: Crear instalador con Inno Setup
echo.
echo [4/5] Creando instalador con Inno Setup...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" setup_installer.iss
if errorlevel 1 (
    echo ERROR: Inno Setup fallo
    pause
    exit /b 1
)
echo OK

REM Paso 5: Resumen
echo.
echo [5/5] Build completado exitosamente!
echo.
echo ============================================================
echo ARCHIVOS GENERADOS:
echo ============================================================
echo.
echo Ejecutable: dist\MetodoBase\MetodoBase.exe
echo Instalador: Output\MetodoBaseSetup_v1.0.0.exe
echo.
echo ============================================================
echo PROXIMOS PASOS:
echo ============================================================
echo.
echo 1. Prueba el ejecutable en otra PC sin Python
echo 2. Prueba el instalador completo
echo 3. Distribuye a los gimnasios
echo.
pause
