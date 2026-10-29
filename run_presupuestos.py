# -*- coding: utf-8 -*-
"""
Lanzador de depuración para el módulo de presupuestos.
Muestra el error exacto si falla algún import o la inicialización de la ventana.
"""

import os, sys, traceback, importlib

# 1) Asegura que el paquete 'presupuestos' sea importable
sys.path.insert(0, r"D:\vah")

# 2) Diagnóstico de PyQt6
try:
    from PyQt6.QtWidgets import QApplication, QMessageBox
except Exception:
    print("\n[ERROR] PyQt6 no se pudo importar:\n")
    traceback.print_exc()
    input("\nPulsa Enter para salir…")
    raise

# 3) Intenta importar el módulo principal
try:
    mod = importlib.import_module("presupuestos.modulo_presupuestos")
except Exception:
    tb = traceback.format_exc()
    print("\n[ERROR] Falló al importar presupuestos.modulo_presupuestos:\n")
    print(tb)
    # Intenta mostrar el error en un cuadro (si ya hay Qt cargado)
    try:
        app = QApplication.instance() or QApplication(sys.argv)
        m = QMessageBox()
        m.setWindowTitle("Error importando modulo_presupuestos")
        m.setIcon(QMessageBox.Icon.Critical)
        m.setText("Ocurrió un error importando el módulo.")
        m.setDetailedText(tb)
        m.exec()
    except Exception:
        pass
    raise

# 4) Si importó bien, lanza el main() o crea la ventana
def _run():
    if hasattr(mod, "main"):
        mod.main()
    else:
        app = QApplication.instance() or QApplication(sys.argv)
        try:
            w = mod.PresupuestosWindow()
            w.show()
            sys.exit(app.exec())
        except Exception:
            tb = traceback.format_exc()
            print("\n[ERROR] Falló al crear/mostrar la ventana:\n")
            print(tb)
            m = QMessageBox()
            m.setWindowTitle("Error al iniciar")
            m.setIcon(QMessageBox.Icon.Critical)
            m.setText("Ocurrió un error al iniciar la ventana.")
            m.setDetailedText(tb)
            m.exec()
            raise

if __name__ == "__main__":
    _run()
