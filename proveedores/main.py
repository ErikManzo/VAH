r"""
Módulo: main.py
Ubicación: D:\vah\proveedores

Punto de entrada para el módulo de Proveedores.
CORREGIDO: Conexión a SQL Server y configuración de geometría.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from common.logger_config import get_logger
from proveedores.art.pantalla_proveedores import PantallaProveedores
from proveedores.data.db import get_connection

logger = get_logger("proveedores.main")


def probar_conexion():
    """Prueba la conexión a SQL Server antes de abrir la interfaz."""
    try:
        conn = get_connection()
        conn.close()
        print("✅ Conexión a SQL Server establecida correctamente.")
        logger.info("Conexion a SQL Server para Proveedores establecida correctamente")
        return True
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        logger.exception("Error de conexion al iniciar Proveedores")
        return False


def main():
    """
    Función principal de arranque de la aplicación de proveedores.
    """
    # Asegurar que la raíz del proyecto esté en el path
    vah_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if os.path.isdir(vah_root) and vah_root not in sys.path:
        sys.path.insert(0, vah_root)

    app = QApplication(sys.argv)

    # Probar conexión
    if not probar_conexion():
        QMessageBox.warning(
            None,
            "Error de Conexión",
            "No se pudo conectar a la base de datos 'proveedores'.\n"
            "Verifique que SQL Server esté en ejecución y que la base de datos exista."
        )
        # Continuar de todas formas, pero puede fallar al guardar

    ventana = PantallaProveedores()
    ventana.show()
    ventana.raise_()
    ventana.activateWindow()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
