#!/usr/bin/env python3
"""
Test rápido de la pantalla de login - Verificación de correcciones 2026-03-28

Este script prueba:
1. Que la ventana de login se carga sin crashes
2. Que los efectos gráficos se aplican correctamente
3. Que las animaciones se comportan según la plataforma

Uso:
    python3 scripts/test_login_visual.py

Nota: Este script muestra la ventana de login en modo standalone.
      NO requiere autenticación real - es solo para verificación visual.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

def verificar_imports():
    """Verificar que todos los imports necesarios están disponibles."""
    print("🔍 Verificando imports...")
    try:
        from ui_desktop.pyside.login_premium import (
            VentanaLoginPremium,
            ResultadoLogin,
            PremiumButton
        )
        from design_system.tokens import Colors, Typography, Spacing, Radius
        print("✅ Todos los imports OK")
        return True
    except ImportError as e:
        print(f"❌ Error de import: {e}")
        return False

def verificar_plataforma(app):
    """Detectar plataforma y características."""
    print("\n🖥️  Información de plataforma:")
    print(f"   Platform: {app.platformName()}")
    
    from ui_desktop.pyside.theme_manager import ThemeManager
    if hasattr(ThemeManager, '_platform_supports_opacity'):
        supports_opacity = ThemeManager._platform_supports_opacity()
        print(f"   Window Opacity: {'✅ Soportado' if supports_opacity else '❌ No soportado'}")
    
    print(f"   Style: {app.style().objectName()}")

def main():
    print("=" * 60)
    print("🧪 TEST VISUAL - LOGIN SCREEN (2026-03-28)")
    print("=" * 60)
    
    if not verificar_imports():
        return 1
    
    # Crear aplicación
    app = QApplication(sys.argv)
    app.setApplicationName("Test Login MetodoBase")
    app.setStyle("Fusion")
    
    verificar_plataforma(app)
    
    # Cargar tema
    print("\n🎨 Cargando tema...")
    try:
        from ui_desktop.pyside.theme_manager import ThemeManager
        ThemeManager.instance().reload()
        print(f"✅ Tema cargado: {ThemeManager.instance().current_theme}")
    except Exception as e:
        print(f"⚠️  Error cargando tema: {e}")
        print("   Continuando sin tema personalizado...")
    
    # Crear ventana de login
    print("\n🚀 Creando ventana de login...")
    try:
        from ui_desktop.pyside.login_premium import VentanaLoginPremium
        login = VentanaLoginPremium()
        
        # Verificar que la ventana tiene las propiedades esperadas
        print(f"   Tamaño: {login.width()}x{login.height()}")
        print(f"   Título: {login.windowTitle()}")
        
        # Verificar componentes críticos
        if hasattr(login, '_login_card'):
            print("   ✅ LoginCard encontrado")
            if hasattr(login._login_card, '_gym_panel'):
                print("   ✅ GymLoginPanel encontrado")
                if hasattr(login._login_card._gym_panel, '_btn_login'):
                    btn = login._login_card._gym_panel._btn_login
                    print(f"   ✅ PremiumButton encontrado")
                    print(f"      - ObjectName: {btn.objectName()}")
                    print(f"      - Glow habilitado: {btn._enable_glow if hasattr(btn, '_enable_glow') else 'N/A'}")
        
        # Mostrar ventana
        print("\n👁️  Mostrando ventana de login...")
        print("   Verifica visualmente:")
        print("   - Los botones tienen sombra/glow")
        print("   - El card tiene sombra")
        print("   - Las animaciones funcionan (si aplica)")
        print("   - Los tabs cambian correctamente")
        print("\n   Presiona ESC o cierra la ventana para salir")
        
        result = login.exec()
        
        print(f"\n📊 Resultado: {result}")
        if result == 0:
            print("   Usuario canceló")
        elif result == 1:
            print("   Login GYM exitoso")
        elif result == 2:
            print("   Login Usuario exitoso")
        
        print("\n✅ Test completado sin crashes")
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
