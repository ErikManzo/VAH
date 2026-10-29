# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Any, Dict

from PyQt6.QtWidgets import QMessageBox, QTextEdit


class FallbackService:
    def buscar_por_tipo(self, **_):
        return []

    def buscar_por_tabla(self, **_):
        return []

    def clientes_buscar(self, *_):
        return []

    def herreria_kg_por_m(self, clave):
        return 0.0

    def paquete_aluminio_items(self, clave_paquete):
        return []

    def paquete_herrajes_items(self, clave_paquete):
        return []

    def obtener_descripcion_material(self, tipo_base, clave_real):
        return f"Componente {clave_real}"


@dataclass
class FallbackEspecificacionesCtx:
    svc: Any
    tipo: str
    clave: str
    color: str | None
    ancho: float
    alto: float
    piezas: int
    ca: float
    ch: float
    extra: Dict[str, Any]


def fallback_dispatch_calculo(ctx):
    return 0.0, 0.0


def fallback_guard_before_add(*_, **__):
    class Result:
        proceed = True
        faltantes = []

    return Result()


def fallback_obtener_partidas_para_vista_previa(ctrl):
    return []


def fallback_calcular_totales_vista_previa(p, d, i):
    return type(
        "FallbackTotalesVistaPrevia",
        (),
        {
            "subtotal_partidas": 0,
            "descuento_porcentaje": 0,
            "descuento_monto": 0,
            "subtotal_con_descuento": 0,
            "iva_porcentaje": 16,
            "iva_monto": 0,
            "total": 0,
        },
    )()


def fallback_redondear_pu_entero_superior(v):
    return v


class FallbackConfiguracionImpresionDialog:
    def __init__(self, d, i, p):
        self.configuracion_aceptada = type("SignalStub", (), {"connect": lambda x: None})()

    def exec(self):
        return 0


class FallbackMessageManager:
    @classmethod
    def error_calculo(cls, p, m):
        pass

    @classmethod
    def info(cls, p, t, m):
        QMessageBox.information(p, t, m)

    @classmethod
    def warning(cls, p, t, m):
        QMessageBox.warning(p, t, m)

    @classmethod
    def critical(cls, p, t, m):
        QMessageBox.critical(p, t, m)

    @classmethod
    def confirmar_dimensiones(cls, p):
        return True

    @classmethod
    def confirmar_guardar_cambios(cls, p):
        return "yes"

    @classmethod
    def placeholder(cls, f):
        pass


class FallbackDatosPresupuesto:
    def __init__(self, **kwargs):
        pass


class FallbackPartidaPresupuesto:
    def __init__(self, **kwargs):
        pass


class FallbackTotalesPresupuesto:
    def __init__(self, **kwargs):
        pass


def fallback_generar_presupuesto_pdf(datos, ruta):
    return False


class FallbackPresupuestoPDFService:
    def __init__(self, svc=None):
        pass

    def generar_pdf_desde_id(self, presupuesto_id):
        return None

    def imprimir_pdf(self, ruta):
        pass


def fallback_habilitar_corrector_para_campos(ventana):
    pass


class FallbackGestionDiccionarioDialog:
    def __init__(self, parent=None):
        pass

    def exec(self):
        pass


class FallbackTextEditConCorrector(QTextEdit):
    pass
