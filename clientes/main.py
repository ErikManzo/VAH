# =========================================================
# Archivo: D:\vah\clientes\main.py
# Descripción: Punto de entrada para el módulo de Clientes
# =========================================================

import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from common.logger_config import get_logger

logger = get_logger("clientes.main")

# ------------------ Configuración de rutas ------------------
# Aseguramos que el directorio raíz del proyecto esté en sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from clientes.art.pantalla_clientes import RegistroClientes
    from clientes.data.db import get_connection
except ImportError as e:
    print("❌ Error al importar la aplicación:", e)
    logger.exception("Error al importar el modulo Clientes")
    sys.exit(1)

# ------------------ Función para verificar conexión ------------------
def probar_conexion():
    try:
        conn = get_connection()
        conn.close()
        return True
    except Exception as e:
        logger.exception("No se pudo conectar a la base de datos de Clientes")
        QMessageBox.warning(
            None,
            "Aviso de conexión",
            f"No se pudo conectar a la base de datos.\n"
            f"La aplicación se ejecutará en modo sin conexión.\n\nDetalles:\n{e}"
        )
        return False

# ------------------ Ejecución de la aplicación ------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Probar conexión antes de abrir la interfaz
    probar_conexion()

    ventana = RegistroClientes()
    ventana.show()

    sys.exit(app.exec())

#
