# -*- coding: utf-8 -*-
import json
import os

from PyQt6.QtWidgets import QMessageBox

from common.app_paths import get_cache_dir
from common.logger_config import get_logger, setup_logger
from presupuestos.integrations.external_launchers import (
    abrir_catalogo_clientes,
    abrir_lista_materiales,
    abrir_modulo_presupuestos_otra_ventana,
    abrir_paquetes_aluminio,
    abrir_paquetes_herrajes,
)
from presupuestos.ui.message_manager import MessageManager

setup_logger("presupuestos.handlers.actions")
logger = get_logger("presupuestos.handlers.actions")


def on_nuevo_presupuesto(window):
    window.presupuesto_ctrl.limpiar_todo()
    window.presupuesto_ctrl.nuevo_presupuesto()
    window._sync_color_rule(from_user=False)


def on_guardar_presupuesto(window):
    window.presupuesto_ctrl.guardar_partida_actual()


def on_guardar_como_presupuesto(window):
    window.presupuesto_ctrl.duplicar_presupuesto_actual()


def on_abrir_presupuesto(window):
    from presupuestos.ui.dialogs.abrir_presupuesto_dialog import AbrirPresupuestoDialog

    dialog = AbrirPresupuestoDialog(window, window.svc)
    if dialog.exec():
        presupuesto_id = dialog.get_selected_id()
        if presupuesto_id:
            window.presupuesto_ctrl.cargar_presupuesto(presupuesto_id)
            window._sync_color_rule(from_user=False)


def on_partida_anterior(window):
    window.presupuesto_ctrl.partida_anterior()
    window._sync_color_rule(from_user=False)


def on_partida_siguiente(window):
    window.presupuesto_ctrl.partida_siguiente()
    window._sync_color_rule(from_user=False)


def on_nueva_partida(window):
    window.presupuesto_ctrl.crear_nueva_partida()
    window._sync_color_rule(from_user=False)


def on_duplicar_partida(window):
    window.presupuesto_ctrl.duplicar_partida_actual()
    window._sync_color_rule(from_user=False)


def on_eliminar_partida(window):
    window.presupuesto_ctrl.eliminar_partida_actual()
    window._sync_color_rule(from_user=False)


def on_exportar_excel(window):
    window.presupuesto_ctrl.exportar_csv()


def on_color_changed(window):
    """Se llama cuando cambia el color global o el color de partida."""
    window.presupuesto_ctrl.recalcular_por_color()


def on_global_dimension_changed(window):
    """Se llama cuando el usuario termina de editar el ancho o alto global."""
    if window._prog:
        return

    if (window.tbl.rowCount() == 0 and window.tbl_he.rowCount() == 0 and window.tbl_paquetes.rowCount() == 0):
        return

    if MessageManager.confirmar_dimensiones(window):
        window.presupuesto_ctrl.aplicar_dimensiones_globales()


def monitor_cliente_nuevo(window):
    """
    Revisa el archivo de caché JSON para ver si se creó un cliente nuevo
    desde el módulo externo de clientes.
    """
    cache_path = os.path.join(get_cache_dir(), "cliente_nuevo.json")
    if not os.path.exists(cache_path):
        return

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        cliente = data.get("cliente_creado")
        if cliente and cliente.get("id") and cliente.get("nombre"):
            window.le_cliente.setText(str(cliente["nombre"]).upper())
            window.cliente_actual_id = cliente["id"]
            window.btn_nuevo_cliente.setEnabled(False)
            window.lst_clientes.clear()
            window.lst_clientes.setVisible(False)

            try:
                os.remove(cache_path)
            except Exception:
                pass

            if hasattr(window, "le_obra") and window.le_obra:
                window.le_obra.setFocus()

            print(f"[DEBUG] Cliente nuevo detectado y pegado: ID {cliente['id']}")
            logger.debug("Cliente nuevo detectado y pegado: ID %s", cliente["id"])
    except (json.JSONDecodeError, IOError) as e:
        print(f"[DEBUG] Error leyendo caché de cliente: {e}")
        logger.warning("Error leyendo cache de cliente: %s", e)
        try:
            os.remove(cache_path)
        except Exception:
            pass


def on_configuracion(window):
    window._on_parametros_sistema()


def on_catalogo_clientes(window):
    """Abre el catálogo de clientes (módulo externo)."""
    abrir_catalogo_clientes(window)


def on_definir_paquetes(window):
    """Abre un diálogo para elegir qué tipo de paquete definir."""
    msg = QMessageBox(window)
    msg.setWindowTitle("Definir Paquetes")
    msg.setText("¿Qué tipo de paquetes desea gestionar?")
    btn_al = msg.addButton("Aluminio", QMessageBox.ButtonRole.ActionRole)
    btn_hr = msg.addButton("Herrajes", QMessageBox.ButtonRole.ActionRole)
    msg.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)

    msg.exec()

    if msg.clickedButton() == btn_al:
        abrir_paquetes_aluminio(window)
    elif msg.clickedButton() == btn_hr:
        abrir_paquetes_herrajes(window)


def on_lista_materiales(window):
    """Abre el concentrador de materiales (ruta corregida)."""
    abrir_lista_materiales(window)


def on_configurar_correo(window):
    from presupuestos.ui.dialogs.configuracion_correo_dialog import ConfiguracionCorreoDialog

    dialog = ConfiguracionCorreoDialog(window.svc, window)
    dialog.exec()


def on_parametros_sistema(window):
    from PyQt6.QtWidgets import QInputDialog, QLineEdit
    from presupuestos.ui.dialogs.parametros_sistema_dialog import ParametrosSistemaDialog

    clave_real = window.svc.obtener_clave_admin()
    if not clave_real:
        logger.warning("Intento de abrir Parametros del Sistema sin clave_admin configurada")
        QMessageBox.warning(
            window,
            "Configuracion requerida",
            "No hay clave de administrador configurada en config.json.\n"
            "Defina una clave segura antes de abrir este dialogo.",
        )
        return

    texto, ok = QInputDialog.getText(
        window,
        "Seguridad",
        "Ingrese la clave de administrador:",
        echo=QLineEdit.EchoMode.Password,
    )

    if not ok:
        return

    if texto != clave_real:
        QMessageBox.critical(window, "Acceso Denegado", "La clave ingresada es incorrecta.")
        return

    dialog = ParametrosSistemaDialog(window.svc, window)
    if dialog.exec():
        window._cargar_ultimo_numero_presupuesto()
        QMessageBox.information(
            window,
            "Información",
            "Parámetros guardados correctamente.\nEl número inicial se aplicará en nuevos presupuestos.",
        )


def editar_desperdicio_global(window):
    from presupuestos.ui.dialogs.editar_valores_globales_dialog import EditarDesperdicioDialog

    print("[DEBUG] editar_desperdicio_global: inicio")
    logger.debug("editar_desperdicio_global: inicio")

    if not window.le_cliente.text().strip():
        QMessageBox.warning(window, "Cliente requerido",
                            "Debe seleccionar un cliente antes de editar el desperdicio global.\n"
                            "Escriba el nombre del cliente o use el catálogo de clientes.")
        return

    if not window.presupuesto_ctrl.presupuesto_id:
        print("[DEBUG] Presupuesto sin ID, guardando silenciosamente...")
        logger.debug("Presupuesto sin ID, guardando silenciosamente antes de editar desperdicio global")
        if not window.presupuesto_ctrl.guardar_partida_actual_silencioso():
            QMessageBox.critical(window, "Error",
                                 "No se pudo guardar el presupuesto actual.\n"
                                 "Verifique los datos del cliente y vuelva a intentar.")
            return
        print(f"[DEBUG] Presupuesto guardado con ID {window.presupuesto_ctrl.presupuesto_id}")
        logger.debug("Presupuesto guardado con ID %s", window.presupuesto_ctrl.presupuesto_id)

    valor_actual = float(window.sb_desperdicio.value())
    print(f"[DEBUG] Valor actual en UI: {valor_actual}")
    logger.debug("Valor actual de desperdicio en UI: %s", valor_actual)
    dialog = EditarDesperdicioDialog(valor_actual, window)
    if not dialog.exec():
        print("[DEBUG] Diálogo cancelado")
        logger.debug("Dialogo de desperdicio global cancelado")
        return

    nuevo_valor = dialog.get_valor()
    print(f"[DEBUG] Nuevo valor: {nuevo_valor}")
    logger.debug("Nuevo valor de desperdicio global: %s", nuevo_valor)

    original_prog = getattr(window, '_prog', False)
    window._prog = False
    try:
        if not window._actualizar_valor_global_partidas("desperdicio", nuevo_valor):
            QMessageBox.critical(window, "Error",
                                 "No se pudo actualizar el desperdicio global.\n"
                                 "Asegúrese de que el presupuesto tenga partidas guardadas.")
            return

        if not window._recalcular_y_persistir_totales_presupuesto_actual():
            QMessageBox.critical(window, "Error",
                                 "No se pudo recalcular los totales globales.\n"
                                 "Los valores pueden estar inconsistentes.")
            return

        window.sb_desperdicio.setValue(nuevo_valor)
        window._on_recalcular_todo()
        window._recalc_summary()

        QMessageBox.information(window, "Éxito",
                                f"Desperdicio actualizado a {nuevo_valor:.2f}% en todas las partidas del presupuesto actual.\n"
                                "Todos los cálculos han sido actualizados y guardados.")
    finally:
        window._prog = original_prog if original_prog else False


def editar_fv_global(window):
    from presupuestos.ui.dialogs.editar_valores_globales_dialog import EditarFVDialog

    print("[DEBUG] editar_fv_global: inicio")
    logger.debug("editar_fv_global: inicio")

    if not window.le_cliente.text().strip():
        QMessageBox.warning(window, "Cliente requerido",
                            "Debe seleccionar un cliente antes de editar el F.V. global.\n"
                            "Escriba el nombre del cliente o use el catálogo de clientes.")
        return

    if not window.presupuesto_ctrl.presupuesto_id:
        print("[DEBUG] Presupuesto sin ID, guardando silenciosamente...")
        logger.debug("Presupuesto sin ID, guardando silenciosamente antes de editar F.V. global")
        if not window.presupuesto_ctrl.guardar_partida_actual_silencioso():
            QMessageBox.critical(window, "Error",
                                 "No se pudo guardar el presupuesto actual.\n"
                                 "Verifique los datos del cliente y vuelva a intentar.")
            return
        print(f"[DEBUG] Presupuesto guardado con ID {window.presupuesto_ctrl.presupuesto_id}")
        logger.debug("Presupuesto guardado con ID %s", window.presupuesto_ctrl.presupuesto_id)

    valor_actual = float(window.sb_fv_pct.value())
    print(f"[DEBUG] Valor actual en UI: {valor_actual}")
    logger.debug("Valor actual de F.V. en UI: %s", valor_actual)
    dialog = EditarFVDialog(valor_actual, window)
    if not dialog.exec():
        logger.debug("Dialogo de F.V. global cancelado")
        return

    nuevo_valor = dialog.get_valor()
    print(f"[DEBUG] Nuevo valor: {nuevo_valor}")
    logger.debug("Nuevo valor de F.V. global: %s", nuevo_valor)

    original_prog = getattr(window, '_prog', False)
    window._prog = False
    try:
        if not window._actualizar_valor_global_partidas("fv_porcentaje", nuevo_valor):
            QMessageBox.critical(window, "Error",
                                 "No se pudo actualizar el F.V. global.\n"
                                 "Asegúrese de que el presupuesto tenga partidas guardadas.")
            return

        if not window._recalcular_y_persistir_totales_presupuesto_actual():
            QMessageBox.critical(window, "Error",
                                 "No se pudo recalcular los totales globales.\n"
                                 "Los valores pueden estar inconsistentes.")
            return

        window.sb_fv_pct.setValue(nuevo_valor)
        window._on_recalcular_todo()
        window._recalc_summary()

        QMessageBox.information(window, "Éxito",
                                f"F.V. actualizado a {nuevo_valor:.2f}% en todas las partidas del presupuesto actual.\n"
                                "Todos los cálculos han sido actualizados y guardados.")
    finally:
        window._prog = original_prog if original_prog else False


def on_gestionar_diccionario(window):
    """Abre el diálogo de gestión del diccionario personalizado."""
    from presupuestos.modulo_presupuestos import (
        CORRECTOR_AVAILABLE,
        SPELLCHECKER_AVAILABLE,
        GestionDiccionarioDialog,
    )

    if CORRECTOR_AVAILABLE and SPELLCHECKER_AVAILABLE:
        dialog = GestionDiccionarioDialog(window)
        dialog.exec()
    else:
        MessageManager.warning(
            window,
            "No disponible",
            "El corrector ortográfico no está disponible.\n\nEjecute: pip install pyspellchecker",
        )


def on_acerca_de(window):
    about_text = """<h3>VAH - Sistema de Presupuestos</h3>
<p><b>Versión:</b> 3.8.0</p>
<p><b>Mejoras:</b> Corrección completa de impresión de TODAS las partidas</p>
<p><b>Corrector Ortográfico Profesional con Diccionario Personalizado</b></p>
<ul>
<li>Subrayado en rojo de palabras mal escritas</li>
<li>Sugerencias automáticas al hacer clic derecho</li>
<li>Agregar palabras nuevas al diccionario personalizado</li>
<li>Gestión del diccionario desde menú Ayuda</li>
<li>Soporte para español (México)</li>
<li>Alto rendimiento incluso con textos largos</li>
<li>CORREGIDO: Escritura al revés en OBRA y TÍTULO</li>
<li>CORREGIDO: Todas las palabras en rojo</li>
</ul>
<hr>
<p>Sistema integral para gestión de presupuestos en aluminio y herrería.</p>"""
    QMessageBox.about(window, "Acerca de VAH", about_text)


def on_nueva_ventana(window):
    abrir_modulo_presupuestos_otra_ventana(window)


def on_cerrar_ventana(window):
    window.close()
