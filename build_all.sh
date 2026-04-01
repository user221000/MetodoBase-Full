#!/usr/bin/env bash
# build_all.sh — Build script para MetodoBase (Linux / macOS)
#
# Uso:
#   ./build_all.sh           # Build para la plataforma actual
#   ./build_all.sh macos     # Build .app + .dmg para macOS

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

VERSION=$(python -c "from config.constantes import VERSION; print(VERSION)")
echo "=== MetodoBase Build v${VERSION} ==="

# Activar venv si existe
if [[ -d ".venv" ]]; then
    source .venv/bin/activate
fi

# Ofuscación opcional de core/licencia.py
if python -c "from build_config import OFUSCAR_LICENCIA; exit(0 if OFUSCAR_LICENCIA else 1)" 2>/dev/null; then
    echo ">>> Ofuscando core/licencia.py con PyArmor..."
    if [[ ! -f "core/licencia.py.orig" ]]; then
        cp core/licencia.py core/licencia.py.orig
    fi
    python -m pyarmor gen --output dist_obf core/licencia.py
    cp dist_obf/licencia.py core/licencia.py
    echo "✅ Ofuscación completada"
fi

TARGET="${1:-default}"

case "$TARGET" in
    macos)
        echo ">>> Build macOS (.app + .dmg)"
        pyinstaller MetodoBase.spec --noconfirm --clean

        # Crear .dmg con create-dmg (brew install create-dmg)
        if command -v create-dmg &>/dev/null; then
            echo ">>> Creando .dmg..."
            mkdir -p Output
            create-dmg \
                --volname "Método Base" \
                --window-pos 200 120 \
                --window-size 600 400 \
                --icon-size 100 \
                --icon "MetodoBase.app" 150 190 \
                --app-drop-link 450 185 \
                "Output/MetodoBase_v${VERSION}.dmg" \
                "dist/MetodoBase.app" || echo "⚠️  create-dmg falló — .app generado en dist/"
        else
            echo "⚠️  create-dmg no encontrado. Instala con: brew install create-dmg"
            echo "    El .app está en dist/MetodoBase.app"
        fi
        ;;
    *)
        echo ">>> Build PyInstaller estándar"
        pyinstaller MetodoBase.spec --noconfirm --clean
        echo "✅ Build completado en dist/MetodoBase/"
        ;;
esac

# Restaurar licencia.py original si fue ofuscada
if [[ -f "core/licencia.py.orig" ]]; then
    cp core/licencia.py.orig core/licencia.py
    echo ">>> Restaurada core/licencia.py original"
fi

echo "=== Build finalizado ==="
