# -*- coding: utf-8 -*-
"""Diálogo para configuración de parámetros del sistema."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QMessageBox, QDialogButtonBox,
    QComboBox, QDoubleSpinBox, QSpinBox, QSizePolicy, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from presupuestos.service import Service
from presupuestos.core.constants import ICON_PATH, COLORES_GLOBAL
from common.focus_utils import install_auto_popup_on_focus


class ParametrosSistemaDialog(QDialog):
    """
    Diálogo para configurar parámetros del sistema.
    """

    def __init__(self, svc: Service, parent=None):
        super().__init__(parent)
        self.svc = svc
        self.setWindowTitle("Parámetros del Sistema")
        self.setModal(True)
        self.setMinimumWidth(500)
        if ICON_PATH and os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        self._build_ui()
        self._combo_popup = install_auto_popup_on_focus(self)
        self._cargar_parametros()

    def _build_ui(self):
        """Construye la interfaz del diálogo."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # Formulario
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Número inicial de presupuesto
        self.sp_numero_inicial = QSpinBox()
        self.sp_numero_inicial.setRange(1, 999999)
        self.sp_numero_inicial.setValue(1)
        self.sp_numero_inicial.setToolTip("Número con el que comenzarán los nuevos presupuestos")
        form_layout.addRow("Número inicial:", self.sp_numero_inicial)

        # Color Global por defecto
        self.cbo_color_defecto = QComboBox()
        self.cbo_color_defecto.addItems(COLORES_GLOBAL)
        form_layout.addRow("Color Global (defecto):", self.cbo_color_defecto)

        # Desperdicio por defecto
        self.sp_desperdicio_defecto = QDoubleSpinBox()
        self.sp_desperdicio_defecto.setRange(0, 100)
        self.sp_desperdicio_defecto.setSuffix(" %")
        form_layout.addRow("Desperdicio (defecto):", self.sp_desperdicio_defecto)

        # Factor de Venta por defecto
        self.sp_fv_defecto = QDoubleSpinBox()
        self.sp_fv_defecto.setRange(0, 1000)
        self.sp_fv_defecto.setSuffix(" %")
        form_layout.addRow("F.V. (defecto):", self.sp_fv_defecto)

        # IVA (%)
        self.sp_iva_porcentaje = QDoubleSpinBox()
        self.sp_iva_porcentaje.setRange(0.0, 100.0)
        self.sp_iva_porcentaje.setDecimals(2)
        self.sp_iva_porcentaje.setValue(16.0)
        self.sp_iva_porcentaje.setSuffix(" %")
        form_layout.addRow("IVA (%):", self.sp_iva_porcentaje)

        # Clave de administrador
        self.edit_clave_admin = QLineEdit()
        self.edit_clave_admin.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_clave_admin.setPlaceholderText("Nueva clave de seguridad")
        form_layout.addRow("Clave Administrador:", self.edit_clave_admin)

        self._ajustar_ancho_controles(form_layout)
        main_layout.addLayout(form_layout)

        # Botones
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Reset
        )
        button_box.button(QDialogButtonBox.StandardButton.Reset).setText("Restaurar por defecto")
        button_box.accepted.connect(self._guardar)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(self._restaurar_por_defecto)
        main_layout.addWidget(button_box)

    def _ajustar_ancho_controles(self, form_layout: QFormLayout):
        """Uniforma el ancho visual de los campos y etiquetas del formulario."""
        field_width = 250
        label_width = 150

        fields = [
            self.sp_numero_inicial,
            self.cbo_color_defecto,
            self.sp_desperdicio_defecto,
            self.sp_fv_defecto,
            self.sp_iva_porcentaje,
            self.edit_clave_admin,
        ]

        for field in fields:
            field.setMinimumWidth(field_width)
            field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            label = form_layout.labelForField(field)
            if label is not None:
                label.setMinimumWidth(label_width)
                label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def _cargar_parametros(self):
        """Carga los parámetros actuales desde la base de datos y config.json."""
        try:
            params = self.svc.obtener_parametros_sistema()
            self.sp_numero_inicial.setValue(self.svc.obtener_numero_presupuesto_inicial())

            idx_color = self.cbo_color_defecto.findText(params.get('color_global_defecto', 'VARIOS'))
            if idx_color >= 0:
                self.cbo_color_defecto.setCurrentIndex(idx_color)

            self.sp_desperdicio_defecto.setValue(params.get('desperdicio_defecto', 2.0))
            self.sp_fv_defecto.setValue(params.get('fv_defecto', 25.0))
            self.sp_iva_porcentaje.setValue(float(params.get('iva_porcentaje', 16.0)))

            self.edit_clave_admin.setText(self.svc.obtener_clave_admin() or "")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al cargar parámetros: {str(e)}")
        finally:
            self.adjustSize()

    def _restaurar_por_defecto(self):
        """Restaura los valores por defecto."""
        self.sp_numero_inicial.setValue(6923)
        self.cbo_color_defecto.setCurrentText("VARIOS")
        self.sp_desperdicio_defecto.setValue(2.0)
        self.sp_fv_defecto.setValue(25.0)
        self.sp_iva_porcentaje.setValue(16.0)

        QMessageBox.information(self, "Restaurado",
                                "Los valores han sido restaurados a los valores por defecto.\nPresione Guardar para aplicar los cambios.")

    def _guardar(self):
        """Guarda los parámetros en la base de datos."""
        parametros = self.svc.obtener_parametros_sistema()
        parametros.update({
            'numero_inicial_presupuesto': self.sp_numero_inicial.value(),
            'color_global_defecto': self.cbo_color_defecto.currentText(),
            'desperdicio_defecto': self.sp_desperdicio_defecto.value(),
            'fv_defecto': self.sp_fv_defecto.value(),
            'iva_porcentaje': self.sp_iva_porcentaje.value(),
        })

        if self.svc.guardar_parametros_sistema(parametros):
            numero_ok = self.svc.cambiar_numero_presupuesto_inicial(self.sp_numero_inicial.value())
            nueva_clave = self.edit_clave_admin.text().strip()
            clave_ok = True
            if nueva_clave:
                clave_ok = self.svc.cambiar_clave_admin(nueva_clave)

            if numero_ok and clave_ok:
                QMessageBox.information(self, "Éxito",
                                        "Parámetros guardados correctamente.")
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    "Guardado parcial",
                    "Se guardaron los parámetros en la base de datos, pero no se pudo actualizar config.json."
                )
        else:
            QMessageBox.critical(self, "Error", "No se pudieron guardar los parámetros.")