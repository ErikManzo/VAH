# -*- coding: utf-8 -*-
import os

from PyQt6.QtWidgets import QMessageBox


def obtener_presupuesto_id_actual(window):
    """Obtiene el ID del presupuesto actual desde el controlador."""
    if hasattr(window, "presupuesto_ctrl"):
        if hasattr(window.presupuesto_ctrl, "presupuesto_actual_id"):
            return window.presupuesto_ctrl.presupuesto_actual_id
        elif hasattr(window.presupuesto_ctrl, "presupuesto_id"):
            return window.presupuesto_ctrl.presupuesto_id

    try:
        num_presupuesto = window.sp_presupuesto.value()
        if num_presupuesto > 0:
            with window.svc.cursor() as cur:
                cur.execute("SELECT id FROM presupuestos WHERE presupuesto = ?", (num_presupuesto,))
                row = cur.fetchone()
                if row:
                    return row[0]
    except Exception as e:
        print(f"[ID] Error obteniendo ID por número: {e}")

    return None


def on_vista_previa(window):
    """Vista previa del PDF - delega en PresupuestoPDFService."""
    from presupuestos.modulo_presupuestos import PDF_GENERATOR_AVAILABLE

    if not PDF_GENERATOR_AVAILABLE:
        QMessageBox.warning(window, "Error", "ReportLab no instalado. Ejecute: pip install reportlab")
        return

    if hasattr(window, "presupuesto_ctrl") and window.presupuesto_ctrl:
        window.presupuesto_ctrl.guardar_partida_actual()

    presupuesto_id = window._obtener_presupuesto_id_actual()

    print(f"[DEBUG] ID del presupuesto actual: {presupuesto_id}")

    if presupuesto_id is None:
        QMessageBox.warning(window, "Error", "No hay un presupuesto cargado para imprimir")
        return

    if window.pdf_service is None:
        QMessageBox.warning(window, "Error", "Servicio de PDF no disponible")
        return

    ruta_pdf = window.pdf_service.generar_pdf_desde_id(presupuesto_id, parent=window)

    if ruta_pdf:
        print(f"[Vista Previa] PDF generado: {ruta_pdf}")
        os.startfile(ruta_pdf)
    else:
        QMessageBox.warning(
            window,
            "Error",
            "No se pudo generar el PDF.\nVerifique que el presupuesto tenga partidas.",
        )


def on_enviar_correo(window):
    """Envía el presupuesto actual por correo."""
    from presupuestos.modulo_presupuestos import PDF_GENERATOR_AVAILABLE
    from presupuestos.ui.dialogs.enviar_correo_dialog import EnviarCorreoDialog

    if not PDF_GENERATOR_AVAILABLE:
        QMessageBox.warning(window, "Error", "ReportLab no instalado. No se puede generar el PDF.")
        return

    if hasattr(window, "presupuesto_ctrl") and window.presupuesto_ctrl:
        window.presupuesto_ctrl.guardar_partida_actual()

    presupuesto_id = window._obtener_presupuesto_id_actual()

    if presupuesto_id is None:
        QMessageBox.warning(window, "Error", "No hay un presupuesto cargado para enviar")
        return

    if window.pdf_service is None:
        QMessageBox.warning(window, "Error", "Servicio de PDF no disponible")
        return

    ruta_pdf = window.pdf_service.generar_pdf_desde_id(presupuesto_id, parent=window)

    if not ruta_pdf:
        QMessageBox.warning(
            window,
            "Error",
            "No se pudo generar el PDF.\nVerifique que el presupuesto tenga partidas.",
        )
        return

    cliente_nombre = window.le_cliente.text().strip()
    cliente_id = getattr(window, "cliente_actual_id", None)
    correo_cliente = ""

    if cliente_id:
        try:
            with window.svc.cursor() as cur:
                cur.execute("SELECT correo FROM [clientes].dbo.clientes WHERE id = ?", (cliente_id,))
                row = cur.fetchone()
                if row and row[0]:
                    correo_cliente = row[0]
        except Exception as e:
            print(f"[Correo] Error obteniendo correo del cliente: {e}")

    dialog = EnviarCorreoDialog(
        parent=window,
        service=window.svc,
        destinatario=correo_cliente,
        presupuesto_num=window.sp_presupuesto.value(),
        cliente=cliente_nombre,
        cliente_id=cliente_id,
        ruta_pdf=ruta_pdf,
    )
    dialog.exec()


def on_imprimir(window):
    window._on_vista_previa()


def on_exportar_pdf(window):
    window._on_vista_previa()


def on_reporte_presupuesto(window):
    window._on_vista_previa()
