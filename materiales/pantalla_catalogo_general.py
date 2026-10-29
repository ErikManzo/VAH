# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QPushButton, QLabel, QWidget, QApplication, QMessageBox
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtCore import Qt
import sys
import os

from common.app_paths import get_resource_path
from common.estilos import aplicar_estilo
from presupuestos.integrations.external_launchers import (
    abrir_materiales_aluminio,
    abrir_materiales_herrajes,
    abrir_materiales_herreria,
    abrir_materiales_otros,
    abrir_materiales_plasticos,
    abrir_materiales_vidrio,
)

class CatalogoGeneralWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        aplicar_estilo(self)
        self.setWindowTitle("Catálogo de Materiales - Selección de Almacén")
        
        for icon_name in ("logo_00001.ico", "logo.jpg", "logo.png"):
            logo_path = get_resource_path(icon_name)
            if os.path.exists(logo_path):
                from PyQt6.QtGui import QIcon
                self.setWindowIcon(QIcon(logo_path))
                break

        self.resize(450, 650)
        
        # Configuración de estilo de ventana
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(245, 246, 250))
        self.setPalette(palette)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(35, 35, 35, 35)
        layout.setSpacing(15)
        
        # Título Principal
        title = QLabel("📦 CATÁLOGO DE MATERIALES")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2f3640; margin-bottom: 5px;")
        layout.addWidget(title)

        subtitle = QLabel("Gestión Integral de Almacenes")
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #7f8c8d; margin-bottom: 25px;")
        layout.addWidget(subtitle)
        
        # Botones de Almacenes con colores institucionales
        self._crear_boton_almacen("🔷 ALUMINIO", "aluminio/pantalla_materiales_aluminio.py", layout, "#2980b9")
        self._crear_boton_almacen("🔩 HERRAJES", "herrajes/pantalla_herrajes.py", layout, "#7f8c8d")
        self._crear_boton_almacen("🔧 HERRERÍA", "herreria/pantalla_herreria.py", layout, "#d35400")
        self._crear_boton_almacen("🪟 VIDRIO", "vidrio/pantalla_vidrio.py", layout, "#16a085")
        self._crear_boton_almacen("🧪 PLÁSTICOS", "plasticos/pantalla_plasticos.py", layout, "#8e44ad")
        self._crear_boton_almacen("📦 OTROS", "otros/pantalla_otros.py", layout, "#2c3e50")
        
        layout.addStretch()

        # Botón Cerrar
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setFixedHeight(45)
        btn_cerrar.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        btn_cerrar.clicked.connect(self.close)
        layout.addWidget(btn_cerrar)
    
    def _crear_boton_almacen(self, texto, ruta_relativa, layout, color):
        btn = QPushButton(texto)
        btn.setFixedHeight(60)
        btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding-left: 25px;
                background-color: {color};
                color: white;
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {color};
                border: 2px solid #ffffff;
            }}
        """)
        btn.clicked.connect(lambda: self._abrir_modulo(ruta_relativa))
        layout.addWidget(btn)
    
    def _abrir_modulo(self, ruta_relativa):
        launchers = {
            "aluminio/pantalla_materiales_aluminio.py": abrir_materiales_aluminio,
            "herrajes/pantalla_herrajes.py": abrir_materiales_herrajes,
            "herreria/pantalla_herreria.py": abrir_materiales_herreria,
            "vidrio/pantalla_vidrio.py": abrir_materiales_vidrio,
            "plasticos/pantalla_plasticos.py": abrir_materiales_plasticos,
            "otros/pantalla_otros.py": abrir_materiales_otros,
        }
        launcher = launchers.get(ruta_relativa.replace("\\", "/"))
        if launcher and launcher(self):
            return
        QMessageBox.warning(self, "No encontrado", f"No se pudo resolver el módulo:\n{ruta_relativa}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CatalogoGeneralWindow()
    window.show()
    sys.exit(app.exec())
