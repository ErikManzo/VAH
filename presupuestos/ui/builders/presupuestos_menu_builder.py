# -*- coding: utf-8 -*-
from PyQt6.QtGui import QAction, QKeySequence

from common.manuales import abrir_manual_pdf

def build_presupuestos_menu(window) -> None:
    mb = window.menuBar()
    mb.clear()

    # =========================================================================
    # ARCHIVO
    # =========================================================================
    m_archivo = mb.addMenu("&Archivo")

    act_nuevo = QAction("&Nuevo Presupuesto", window, shortcut=QKeySequence("Ctrl+N"),
                        triggered=window._on_nuevo_presupuesto)
    m_archivo.addAction(act_nuevo)

    act_abrir = QAction("&Abrir Presupuesto", window, shortcut=QKeySequence("Ctrl+O"),
                        triggered=window._on_abrir_presupuesto)
    m_archivo.addAction(act_abrir)

    m_archivo.addSeparator()

    act_guardar = QAction("&Guardar Presupuesto", window, shortcut=QKeySequence("Ctrl+S"),
                          triggered=window._on_guardar_presupuesto)
    m_archivo.addAction(act_guardar)

    act_guardar_como = QAction("&Guardar Como...", window, shortcut=QKeySequence("Ctrl+Shift+S"),
                               triggered=window._on_guardar_como_presupuesto)
    m_archivo.addAction(act_guardar_como)

    m_archivo.addSeparator()

    act_imprimir = QAction("&Imprimir", window, shortcut=QKeySequence("Ctrl+P"),
                           triggered=window._on_imprimir)
    m_archivo.addAction(act_imprimir)

    act_vista_previa = QAction("Vista &Previa de Impresión", window,
                               triggered=window._on_vista_previa)
    m_archivo.addAction(act_vista_previa)

    m_archivo.addSeparator()

    act_exportar_excel = QAction("Exportar a E&xcel", window, shortcut=QKeySequence("Ctrl+E"),
                                 triggered=window._on_exportar_excel)
    m_archivo.addAction(act_exportar_excel)

    act_exportar_pdf = QAction("Exportar a &PDF", window, shortcut=QKeySequence("Ctrl+D"),
                               triggered=window._on_exportar_pdf)
    m_archivo.addAction(act_exportar_pdf)

    act_enviar_correo = QAction("Enviar por &Correo", window, shortcut=QKeySequence("Ctrl+M"),
                                triggered=window._on_enviar_correo)
    m_archivo.addAction(act_enviar_correo)

    m_archivo.addSeparator()

    act_salir = QAction("&Salir", window, shortcut=QKeySequence("Ctrl+Q"), triggered=window.close)
    m_archivo.addAction(act_salir)

    # =========================================================================
    # PRESUPUESTO
    # =========================================================================
    m_presupuesto = mb.addMenu("&Presupuesto")

    act_nueva_partida = QAction("Nueva &Partida", window, shortcut=QKeySequence("Ctrl+T"),
                                triggered=window._on_nueva_partida)
    m_presupuesto.addAction(act_nueva_partida)

    act_duplicar_partida = QAction("&Duplicar Partida", window, triggered=window._on_duplicar_partida)
    m_presupuesto.addAction(act_duplicar_partida)

    act_eliminar_partida = QAction("&Eliminar Partida", window, shortcut=QKeySequence("Del"),
                                   triggered=window._on_eliminar_partida)
    m_presupuesto.addAction(act_eliminar_partida)

    m_presupuesto.addSeparator()

    act_editar_desperdicio_global = QAction("Editar &Desperdicio Global...", window,
                                            triggered=window._editar_desperdicio_global)
    m_presupuesto.addAction(act_editar_desperdicio_global)

    act_editar_fv_global = QAction("Editar &F.V. Global...", window,
                                   triggered=window._editar_fv_global)
    m_presupuesto.addAction(act_editar_fv_global)

    m_presupuesto.addSeparator()

    act_recalcular_todo = QAction("&Recalcular Todo", window, shortcut=QKeySequence("F5"),
                                  triggered=window._on_recalcular_todo)
    m_presupuesto.addAction(act_recalcular_todo)

    # =========================================================================
    # MANTENIMIENTO
    # =========================================================================
    m_mantenimiento = mb.addMenu("&Mantenimiento")

    act_catalogo_materiales = QAction("&Catálogo de Materiales", window, triggered=window._on_catalogo_materiales)
    m_mantenimiento.addAction(act_catalogo_materiales)

    act_catalogo_clientes = QAction("Catálogo de &Clientes", window, triggered=window._on_catalogo_clientes)
    m_mantenimiento.addAction(act_catalogo_clientes)

    m_mantenimiento.addSeparator()

    act_definir_paquetes = QAction("Definir &Paquetes", window, triggered=window._on_definir_paquetes)
    m_mantenimiento.addAction(act_definir_paquetes)

    act_configurar_correo = QAction("Configurar &Correo", window, triggered=window._on_configurar_correo)
    m_mantenimiento.addAction(act_configurar_correo)

    act_parametros_sistema = QAction("&Parámetros del Sistema", window, triggered=window._on_parametros_sistema)
    m_mantenimiento.addAction(act_parametros_sistema)

    # =========================================================================
    # REPORTES
    # =========================================================================
    m_reportes = mb.addMenu("&Reportes")

    act_reporte_presupuesto = QAction("&Reporte de Presupuesto", window, triggered=window._on_reporte_presupuesto)
    m_reportes.addAction(act_reporte_presupuesto)

    act_lista_materiales = QAction("&Lista de Materiales", window, triggered=window._on_lista_materiales)
    m_reportes.addAction(act_lista_materiales)

    # =========================================================================
    # VENTANA
    # =========================================================================
    m_ventana = mb.addMenu("&Ventana")

    act_nueva_ventana = QAction("&Nueva Ventana", window, triggered=window._on_nueva_ventana)
    m_ventana.addAction(act_nueva_ventana)

    act_cerrar_ventana = QAction("&Cerrar Ventana", window, triggered=window._on_cerrar_ventana)
    m_ventana.addAction(act_cerrar_ventana)

    # =========================================================================
    # AYUDA
    # =========================================================================
    m_ayuda = mb.addMenu("&Ayuda")

    act_manual_operativo = QAction("&Manual Operativo", window,
                                   triggered=lambda: abrir_manual_pdf("Presupuestos", "operativo", window))
    m_ayuda.addAction(act_manual_operativo)

    act_manual_tecnico = QAction("Manual &Tecnico", window,
                                 triggered=lambda: abrir_manual_pdf("Presupuestos", "tecnico", window))
    m_ayuda.addAction(act_manual_tecnico)

    m_ayuda.addSeparator()

    act_acerca_de = QAction("&Acerca de VAH", window, triggered=window._on_acerca_de)
    m_ayuda.addAction(act_acerca_de)

    m_ayuda.addSeparator()

    act_gestionar_diccionario = QAction("&Gestionar Diccionario Personalizado", window,
                                        triggered=window._on_gestionar_diccionario)
    m_ayuda.addAction(act_gestionar_diccionario)

    # Se conserva la duplicación actual por compatibilidad exacta con el estado vigente.
    act_gestionar_diccionario = QAction("&Gestionar Diccionario Personalizado", window,
                                        triggered=window._on_gestionar_diccionario)
    m_ayuda.addAction(act_gestionar_diccionario)
