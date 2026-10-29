# -*- coding: utf-8 -*-
"""
VAH — Pantalla Principal (versión corregida para empaquetado)
CORRECCIÓN: launch_unique() ahora detecta ventanas cerradas (no visibles)
y las reemplaza por nuevas instancias, permitiendo reabrir módulos
después de cerrarlos con la X.
"""
from __future__ import annotations
import os
import sys
import importlib
from typing import Optional, Dict
from PyQt6.QtCore import Qt, QSize, QPoint, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QAction, QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QMessageBox,
    QTabWidget, QStatusBar, QMenu
)

# ============================================================================
# FORZAR RUTAS EN MODO COMPILADO (antes de importar common)
# ============================================================================
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
    common_path = os.path.join(base_dir, 'common')
    if os.path.isdir(common_path) and common_path not in sys.path:
        sys.path.insert(0, common_path)
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)
    internal = os.path.join(base_dir, '_internal')
    if os.path.isdir(internal) and internal not in sys.path:
        sys.path.insert(0, internal)
else:
    # Modo desarrollo: buscar el directorio raíz del proyecto
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)

    # Si estamos en principal/, subir un nivel
    if os.path.basename(current_dir) == 'principal':
        project_root = os.path.dirname(current_dir)
    else:
        project_root = current_dir

    # Verificar que project_root contiene los módulos esperados
    # Si no, buscar hacia arriba hasta encontrarlo
    while project_root and not (
            os.path.isdir(os.path.join(project_root, 'presupuestos')) and
            os.path.isdir(os.path.join(project_root, 'principal'))
    ):
        parent = os.path.dirname(project_root)
        if parent == project_root:
            break
        project_root = parent

    if project_root not in sys.path:
        sys.path.insert(0, project_root)

# ============================================================================
# IMPORTACIONES (después de ajustar sys.path)
# ============================================================================
from common.app_paths import get_app_root as common_get_app_root, get_resource_path
from common.estilos import QSS_BASE, aplicar_estilo
from common.logger_config import get_logger

logger = get_logger('principal.pantalla')


# ============================================================================
# DETECCIÓN DE ENTORNO Y RUTAS
# ============================================================================
def is_frozen() -> bool:
    return getattr(sys, 'frozen', False)


def get_app_root() -> str:
    return common_get_app_root()


def get_resource_root() -> str:
    if getattr(sys, "_MEIPASS", None):
        return sys._MEIPASS
    return get_app_root()


def resolve_resource_path(*relative_parts: str) -> str:
    return get_resource_path(*relative_parts)


VAH_ROOT = get_app_root()

# ============================================================================
# MAPEO DE MÓDULOS A IMPORTACIONES Y CLASES (CORREGIDO)
# ============================================================================
MODULO_A_CLASE = {
    "clientes": {
        "import": "clientes.art.pantalla_clientes",
        "class": "RegistroClientes"
    },
    "proveedores": {
        "import": "proveedores.art.pantalla_proveedores",
        "class": "PantallaProveedores"
    },
    "presupuestos": {
        "import": "presupuestos.modulo_presupuestos",
        "class": "PresupuestosWindow"
    },
    "cxc": {
        "import": "cxc.art.pantalla_cxc",
        "class": "PantallaCxc"
    },
    "concentrador": {
        "import": "concentrador_materiales.ui.pantalla_concentrador",
        "class": "PantallaConcentrador"
    },
    "aluminio": {
        "import": "materiales.aluminio.pantalla_materiales_aluminio",
        "class": "PantallaMaterialesAluminio"
    },
    "herreria": {
        "import": "materiales.herreria.pantalla_herreria",
        "class": "PantallaHerreria"
    },
    "vidrio": {
        "import": "materiales.vidrio.pantalla_vidrio",
        "class": "PantallaVidrio"
    },
    "herrajes": {
        "import": "materiales.herrajes.pantalla_herrajes",
        "class": "PantallaHerrajes"
    },
    "plasticos": {
        "import": "materiales.plasticos.pantalla_plasticos",
        "class": "PantallaPlasticos"
    },
    "otros": {
        "import": "materiales.otros.pantalla_otros",
        "class": "PantallaOtros"
    },
    "paquetes_aluminio": {
        "import": "paquetes.aluminio.pantalla_paquete_aluminio",
        "class": "PaquetesAluminioUI"
    },
    "paquetes_herrajes": {
        "import": "paquetes.herrajes.pantalla_paquete_herrajes",
        "class": "PaqueteHerrajesUI"
    },
}

# ============================================================================
# ICONOS Y LOGO
# ============================================================================
ICON_CANDIDATES = [
    resolve_resource_path("principal", "pantalla_principal.ico"),
    resolve_resource_path("logo_00001.ico"),
    resolve_resource_path("logo.jpg"),
    resolve_resource_path("logo.png"),
    resolve_resource_path("icono.ico"),
]

LOGO_CANDIDATES = [
    resolve_resource_path("logo_principal.jpg"),
    resolve_resource_path("logo_principal_pagina.jpg"),
    resolve_resource_path("logo.jpg"),
    resolve_resource_path("logo.png"),
    resolve_resource_path("manuales", "imagenes", "comunes", "logo_vah.png"),
]

LOGO_PATH = next((path for path in LOGO_CANDIDATES if os.path.isfile(path)), LOGO_CANDIDATES[0])

# ============================================================================
# ESTILO
# ============================================================================
APP_QSS = QSS_BASE + """
QMenu {
    padding: 6px 0px;
}
QMenu::item {
    padding: 6px 24px 6px 24px;
    background: transparent;
}
QMenu::separator {
    height: 1px;
    background: #e5e7eb;
    margin: 6px 0 6px 0;
}
QStatusBar {
    background: #ffffff;
}
"""


# ============================================================================
# LOGO CENTRADO
# ============================================================================
class CenterLogo(QWidget):
    def __init__(self, logo_path: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._logo_path = logo_path
        self._pixmap_original: Optional[QPixmap] = None
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.addWidget(self.label)

        self._cargar_pixmap()
        self._actualizar_pixmap()

    def _cargar_pixmap(self) -> None:
        if os.path.isfile(self._logo_path):
            pix = QPixmap(self._logo_path)
            if not pix.isNull():
                self._pixmap_original = pix
                return
        self._pixmap_original = QPixmap(1, 1)

    def resizeEvent(self, e) -> None:
        super().resizeEvent(e)
        self._actualizar_pixmap()

    def _actualizar_pixmap(self) -> None:
        if not self._pixmap_original:
            return
        ancho = max(1, int(self.width() * 0.75))
        scaled = self._pixmap_original.scaled(
            QSize(ancho, self.height()),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.label.setPixmap(scaled)


# ============================================================================
# LANZADOR DE MÓDULOS (CORREGIDO: detecta ventanas cerradas)
# ============================================================================
RUNNING: Dict[str, QWidget] = {}


def unregister_running(key: str) -> None:
    RUNNING.pop(key, None)


def launch_unique(module_key: str, title_hint: str, parent: Optional[QWidget], status: Optional[QStatusBar]) -> None:
    """
    Lanza un módulo de forma única. Si ya está abierto y visible, lo trae al frente.
    Si fue cerrado (no visible), lo elimina del registro y crea una nueva instancia.
    Usa importación dinámica (no subprocess) tanto en desarrollo como en compilado.
    """
    # Verificar si ya hay una instancia registrada
    if module_key in RUNNING and RUNNING[module_key] is not None:
        win = RUNNING[module_key]
        if isinstance(win, QWidget):
            # CORRECCIÓN: Si la ventana fue cerrada (no visible), removerla
            # y crear una nueva instancia.
            if not win.isVisible():
                del RUNNING[module_key]
            else:
                # Está visible y abierta, traer al frente
                if win.isMinimized():
                    win.showNormal()
                win.raise_()
                win.activateWindow()
                if status:
                    status.showMessage(f"{title_hint} ya estaba abierto.", 1800)
                return
        else:
            del RUNNING[module_key]

    config = MODULO_A_CLASE.get(module_key)
    if not config:
        QMessageBox.critical(parent, "Error", f"No se encontró configuración para el módulo: {title_hint}")
        return

    try:
        mod = importlib.import_module(config["import"])
        cls = getattr(mod, config["class"])
        ventana = cls()
        if not isinstance(ventana, QWidget):
            raise TypeError(f"La clase {config['class']} no es una subclase de QWidget")
        RUNNING[module_key] = ventana
        ventana.show()
        if status:
            status.showMessage(f"Abriendo {title_hint}...", 1800)
        ventana.destroyed.connect(lambda: unregister_running(module_key))
    except ImportError as e:
        QMessageBox.critical(parent, "Error de importación",
                             f"No se pudo importar el módulo '{config['import']}'.\n\n{str(e)}")
        RUNNING.pop(module_key, None)
    except AttributeError as e:
        QMessageBox.critical(parent, "Error de clase",
                             f"No se encontró la clase '{config['class']}' en el módulo.\n\n{str(e)}")
        RUNNING.pop(module_key, None)
    except Exception as e:
        QMessageBox.critical(parent, "Error inesperado",
                             f"No se pudo abrir {title_hint}:\n\n{str(e)}")
        RUNNING.pop(module_key, None)


def close_all_children(timeout_sec: float = 2.0) -> None:
    """Cierra todas las ventanas hijas abiertas."""
    for key, win in list(RUNNING.items()):
        if isinstance(win, QWidget):
            try:
                win.close()
            except Exception:
                pass
            RUNNING.pop(key, None)


# ============================================================================
# VENTANA PRINCIPAL
# ============================================================================
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        aplicar_estilo(self)
        self.setFont(QFont("Segoe UI", 9))
        self.setWindowTitle("VAH — Pantalla Principal")

        icon = self._load_app_icon()
        if icon is not None:
            self.setWindowIcon(icon)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Listo")

        self.logo = CenterLogo(LOGO_PATH, self)
        self.setCentralWidget(self.logo)

        self.tabs = QTabWidget(self)
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setDocumentMode(True)
        self.setMenuWidget(self.tabs)
        self.tabs.addTab(QWidget(), "Inicio")
        self.tabs.tabBarClicked.connect(self._on_tabbar_clicked)

        QShortcut(QKeySequence("Alt+I"), self, activated=self._show_inicio_menu)

        self._force_maximized()
        self._inicio_menu = self._build_inicio_menu()

    def _build_inicio_menu(self) -> QMenu:
        m = QMenu(self)

        personas = m.addMenu("Personas")
        self._add_action(personas, "Clientes", lambda: launch_unique("clientes", "Clientes", self, self.status),
                         ["Ctrl+Shift+C"])
        self._add_action(personas, "Proveedores",
                         lambda: launch_unique("proveedores", "Proveedores", self, self.status), ["Ctrl+Shift+P"])

        materiales = m.addMenu("Materiales")
        self._add_action(materiales, "Aluminio", lambda: launch_unique("aluminio", "Aluminio", self, self.status),
                         ["Alt+1"])
        self._add_action(materiales, "Herrería", lambda: launch_unique("herreria", "Herrería", self, self.status),
                         ["Alt+2"])
        self._add_action(materiales, "Vidrio", lambda: launch_unique("vidrio", "Vidrio", self, self.status), ["Alt+3"])
        self._add_action(materiales, "Herrajes", lambda: launch_unique("herrajes", "Herrajes", self, self.status),
                         ["Alt+4"])
        self._add_action(materiales, "Plásticos", lambda: launch_unique("plasticos", "Plásticos", self, self.status),
                         ["Alt+5"])
        self._add_action(materiales, "Otros", lambda: launch_unique("otros", "Otros", self, self.status), ["Alt+6"])

        m.addSeparator()

        paquetes = m.addMenu("Paquetes")
        self._add_action(paquetes, "Aluminio",
                         lambda: launch_unique("paquetes_aluminio", "Paquetes Aluminio", self, self.status),
                         ["Ctrl+Alt+A"])
        self._add_action(paquetes, "Herrajes",
                         lambda: launch_unique("paquetes_herrajes", "Paquetes Herrajes", self, self.status),
                         ["Ctrl+Alt+H"])

        m.addSeparator()

        self._add_action(m, "Presupuestos", lambda: launch_unique("presupuestos", "Presupuestos", self, self.status),
                         ["Ctrl+Alt+P"])

        m.addSeparator()

        cxc_menu = m.addMenu("Cuentas por Cobrar (CXC)")
        self._add_action(cxc_menu, "Gestión de CXC",
                         lambda: launch_unique("cxc", "Cuentas por Cobrar", self, self.status), ["Ctrl+Shift+X"])
        self._add_action(cxc_menu, "Explosión de materiales (Concentrador)",
                         lambda: launch_unique("concentrador", "Concentrador de Materiales", self, self.status),
                         ["Ctrl+Shift+E"])

        m.addSeparator()

        self._add_action(m, "Salir de la aplicación", self.close, ["Ctrl+Q"])

        return m

    def _add_action(self, menu, text, slot, shortcuts=None):
        act = QAction(text, self)
        act.triggered.connect(slot)
        if shortcuts:
            act.setShortcuts([QKeySequence(s) for s in shortcuts])
        menu.addAction(act)
        return act

    def _show_inicio_menu(self):
        bar = self.tabs.tabBar()
        rect = bar.tabRect(0)
        global_pos = bar.mapToGlobal(rect.bottomLeft()) + QPoint(0, 2)
        self._inicio_menu.popup(global_pos)

    def _force_maximized(self):
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.availableGeometry())
        self.setWindowState(Qt.WindowState.WindowMaximized)
        QTimer.singleShot(0, self.showMaximized)

    def showEvent(self, e):
        super().showEvent(e)
        self._force_maximized()

    def _on_tabbar_clicked(self, index):
        if index == 0:
            self._show_inicio_menu()

    def closeEvent(self, e):
        try:
            close_all_children(timeout_sec=2.0)
        finally:
            super().closeEvent(e)

    def _load_app_icon(self):
        for path in ICON_CANDIDATES:
            if os.path.isfile(path):
                ico = QIcon(path)
                if not ico.isNull():
                    return ico
        return None


# ============================================================================
# MAIN
# ============================================================================
def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_QSS)

    for icon_path in ICON_CANDIDATES:
        if os.path.isfile(icon_path):
            app.setWindowIcon(QIcon(icon_path))
            break

    win = MainWindow()
    win.show()
    win.showMaximized()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())