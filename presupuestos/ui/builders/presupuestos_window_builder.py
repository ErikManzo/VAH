# -*- coding: utf-8 -*-
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QGroupBox, QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QPushButton, QListWidget, QTableWidget, QHeaderView, QSplitter, QSizePolicy
)
from common.search_utils import configure_list_widget_for_search_results

from presupuestos.core.constants import (
    COLORES_GLOBAL, COLORES_PARTIDA, TIPOS_MATERIAL, TIPOS_BUSQUEDA,
    SPLITTER_LEFT_RATIO, STYLESHEET,
)
from presupuestos.core.utils import (
    connect_upper_lineedit as _connect_upper_lineedit,
    connect_upper_textedit as _connect_upper_textedit,
    connect_upper_combobox as _connect_upper_combobox,
)
from presupuestos.ui.tables.paquetes import TablaPaquetes
from presupuestos.ui.tables.anidada import TablaAnidada


def ensure_focusable_widgets(window) -> None:
    """Asegura que todos los widgets tengan política de foco correcta."""
    focusable_widgets = [
        window.le_cliente, window.le_obra,
        window.le_fecha, window.cbo_color_global, window.le_titulo,
        window.te_desc, window.sb_desperdicio, window.sb_fv_pct, window.cbo_color,
        window.sp_precio_kg, window.sp_ancho, window.sp_alto, window.sp_mo, window.sp_acc,
        window.sb_pzas_global, window.cbo_tipo, window.cbo_buscar, window.le_filtro,
        window.tbl, window.tbl_he, window.tbl_paquetes, window.tbl_anidada,
        window.cbo_partida_rapida
    ]
    for widget in focusable_widgets:
        if widget and hasattr(widget, "setFocusPolicy"):
            if widget.focusPolicy() == Qt.FocusPolicy.NoFocus:
                if not getattr(widget, "isReadOnly", lambda: False)():
                    widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)


def apply_split_20_80(window, splitter_left_ratio: float = SPLITTER_LEFT_RATIO) -> None:
    try:
        if hasattr(window, "split") and window.split is not None:
            w = max(1, window.width())
            left = int(w * splitter_left_ratio)
            right = max(1, w - left)
            sizes = window.split.sizes()
            if not sizes or abs(sizes[0] - left) > 3:
                window.split.setSizes([left, right])
    except Exception:
        pass


def build_presupuestos_window_ui(window, *, busquedas_module, text_edit_cls) -> None:
    """Construye toda la interfaz de usuario sobre la ventana recibida."""
    root = QWidget(window)
    window.setCentralWidget(root)

    rl = QHBoxLayout(root)
    rl.setContentsMargins(8, 8, 8, 8)
    rl.setSpacing(8)

    window.split = QSplitter(Qt.Orientation.Horizontal, window)
    window.split.setHandleWidth(6)
    rl.addWidget(window.split)

    # --- PANEL IZQUIERDO (20%) ---
    left = QWidget(window)
    lv = QVBoxLayout(left)
    lv.setContentsMargins(0, 0, 0, 0)
    lv.setSpacing(8)

    gb_d = QGroupBox("Datos del presupuesto", window)
    g = QGridLayout(gb_d)
    g.setContentsMargins(8, 8, 8, 8)
    g.setSpacing(6)
    r = 0

    g.addWidget(QLabel("CLIENTE:"), r, 0)
    window.le_cliente = QLineEdit(window)
    g.addWidget(window.le_cliente, r, 1)
    r += 1

    window.le_cliente.textEdited.connect(lambda s: busquedas_module.clientes_start_search(window, s))
    _connect_upper_lineedit(window.le_cliente)

    window.btn_nuevo_cliente = QPushButton("Nuevo cliente", window)
    window.btn_nuevo_cliente.clicked.connect(lambda: busquedas_module.nuevo_cliente(window))
    window.btn_nuevo_cliente.setEnabled(False)
    window.btn_nuevo_cliente.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    g.addWidget(window.btn_nuevo_cliente, r, 1)
    r += 1

    window.lst_clientes = QListWidget(window)
    window.lst_clientes.setVisible(False)
    configure_list_widget_for_search_results(window.lst_clientes)
    window.lst_clientes.itemClicked.connect(lambda it: busquedas_module.pick_cliente(window, it))
    busquedas_module.install_cliente_list_filter(window)
    g.addWidget(window.lst_clientes, r, 0, 1, 2)
    r += 1

    g.addWidget(QLabel("OBRA:"), r, 0)
    window.le_obra = text_edit_cls(window)
    window.le_obra.setPlaceholderText("OBRA")
    window.le_obra.setMaximumHeight(60)
    window.le_obra.setMinimumHeight(40)
    window.le_obra.setObjectName("le_obra")
    window.le_obra.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    window.le_obra.customContextMenuRequested.connect(window.le_obra._mostrar_menu)
    g.addWidget(window.le_obra, r, 1)
    r += 1

    g.addWidget(QLabel("PRESUPUESTO:"), r, 0)
    window.sp_presupuesto = QSpinBox(window, minimum=1, maximum=999999)
    window.sp_presupuesto.setValue(1)
    window.sp_presupuesto.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
    window.sp_presupuesto.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    window.sp_presupuesto.setReadOnly(True)
    g.addWidget(window.sp_presupuesto, r, 1)
    r += 1

    g.addWidget(QLabel("PARTIDA:"), r, 0)
    partida_layout = QHBoxLayout()
    partida_layout.setSpacing(4)

    window.cbo_partida_rapida = QComboBox(window)
    window.cbo_partida_rapida.setMinimumWidth(200)
    window.cbo_partida_rapida.setToolTip("Selecciona una partida para navegar rápidamente")
    window.cbo_partida_rapida.setEditable(False)
    window.cbo_partida_rapida.currentIndexChanged.connect(window._on_partida_rapida_seleccionada)
    partida_layout.addWidget(window.cbo_partida_rapida, 2)

    window.sp_partida = QSpinBox(window, minimum=1, maximum=999999)
    window.sp_partida.setValue(1)
    window.sp_partida.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
    window.sp_partida.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    window.sp_partida.setReadOnly(True)
    window.sp_partida.setFixedWidth(60)
    partida_layout.addWidget(window.sp_partida)

    window.btn_partida_anterior = QPushButton("←")
    window.btn_partida_anterior.setFixedWidth(30)
    window.btn_partida_anterior.setToolTip("Partida anterior")
    window.btn_partida_anterior.clicked.connect(window._on_partida_anterior)
    window.btn_partida_anterior.setEnabled(False)
    window.btn_partida_anterior.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    partida_layout.addWidget(window.btn_partida_anterior)

    window.btn_partida_siguiente = QPushButton("→")
    window.btn_partida_siguiente.setFixedWidth(30)
    window.btn_partida_siguiente.setToolTip("Partida siguiente")
    window.btn_partida_siguiente.clicked.connect(window._on_partida_siguiente)
    window.btn_partida_siguiente.setEnabled(False)
    window.btn_partida_siguiente.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    partida_layout.addWidget(window.btn_partida_siguiente)

    g.addLayout(partida_layout, r, 1)
    r += 1

    g.addWidget(QLabel("FECHA:"), r, 0)
    window.le_fecha = QLineEdit(window)
    window.le_fecha.setInputMask("99/99/9999")
    window.le_fecha.setAlignment(Qt.AlignmentFlag.AlignCenter)
    window.le_fecha.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    window.le_fecha.textEdited.connect(window._on_fecha_editado)
    g.addWidget(window.le_fecha, r, 1)
    r += 1

    g.addWidget(QLabel("COLOR:"), r, 0)
    window.cbo_color_global = QComboBox(window)
    window.cbo_color_global.setEditable(True)
    window.cbo_color_global.addItems(COLORES_GLOBAL)
    window.cbo_color_global.currentTextChanged.connect(
        lambda _=None: (getattr(window, "_sync_color_rule", None) and window._sync_color_rule(from_user=True))
    )
    window.cbo_color_global.currentTextChanged.connect(window._on_color_changed)
    g.addWidget(window.cbo_color_global, r, 1)
    r += 1
    _connect_upper_combobox(window.cbo_color_global)

    lv.addWidget(gb_d)

    gb_p = QGroupBox("Datos de la partida", window)
    pv = QVBoxLayout(gb_p)
    pv.setContentsMargins(8, 8, 8, 8)
    pv.setSpacing(6)

    window.le_titulo = text_edit_cls(window)
    window.le_titulo.setPlaceholderText("TÍTULO DE PARTIDA")
    window.le_titulo.setMaximumHeight(60)
    window.le_titulo.setMinimumHeight(40)
    window.le_titulo.setObjectName("le_titulo")
    window.le_titulo.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    window.le_titulo.customContextMenuRequested.connect(window.le_titulo._mostrar_menu)
    pv.addWidget(window.le_titulo)

    window.te_desc = text_edit_cls(window)
    window.te_desc.setPlaceholderText("DESCRIPCIÓN DE LA PARTIDA")
    window.te_desc.setObjectName("te_desc")
    window.te_desc.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    window.te_desc.customContextMenuRequested.connect(window.te_desc._mostrar_menu)
    pv.addWidget(window.te_desc, 1)
    _connect_upper_textedit(window.te_desc)

    lv.addWidget(gb_p)

    gb_v = QGroupBox("Valores de la partida", window)
    gv = QGridLayout(gb_v)
    gv.setContentsMargins(8, 8, 8, 8)
    gv.setSpacing(6)
    gv.setColumnStretch(1, 1)
    rr = 0

    gv.addWidget(QLabel("DESPERDICIO:"), rr, 0)
    window.sb_desperdicio = QDoubleSpinBox(window, decimals=2, minimum=0.0, maximum=100.0)
    window.sb_desperdicio.setValue(2)
    window.sb_desperdicio.setSuffix("%")
    window.sb_desperdicio.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    window.sb_desperdicio.focusInEvent = lambda event: window.sb_desperdicio.selectAll()
    window.sb_desperdicio.valueChanged.connect(window._on_valor_partida_changed)
    gv.addWidget(window.sb_desperdicio, rr, 1)
    rr += 1

    gv.addWidget(QLabel("F.V. (%):"), rr, 0)
    window.sb_fv_pct = QDoubleSpinBox(window, decimals=2, minimum=0.0, maximum=1000.0)
    window.sb_fv_pct.setValue(25)
    window.sb_fv_pct.setSuffix("%")
    window.sb_fv_pct.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    window.sb_fv_pct.focusInEvent = lambda event: window.sb_fv_pct.selectAll()
    window.sb_fv_pct.valueChanged.connect(window._on_valor_partida_changed)
    gv.addWidget(window.sb_fv_pct, rr, 1)
    rr += 1

    window.lbl_color_partida = QLabel("COLOR (PARTIDA):")
    gv.addWidget(window.lbl_color_partida, rr, 0)
    window.cbo_color = QComboBox(window)
    window.cbo_color.setEditable(True)
    window.cbo_color.addItems(COLORES_PARTIDA)
    window.cbo_color.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    if window.cbo_color.lineEdit():
        window.cbo_color.lineEdit().focusInEvent = lambda event: window.cbo_color.lineEdit().selectAll()
    window.cbo_color.currentTextChanged.connect(window._on_color_changed)
    gv.addWidget(window.cbo_color, rr, 1)
    rr += 1
    _connect_upper_combobox(window.cbo_color)

    window.lbl_precio_kg = QLabel("$ / KG:")
    gv.addWidget(window.lbl_precio_kg, rr, 0)
    window.sp_precio_kg = QDoubleSpinBox(window, decimals=2, minimum=0.0, maximum=99999999.99)
    window.sp_precio_kg.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    window.sp_precio_kg.focusInEvent = lambda event: window.sp_precio_kg.selectAll()
    gv.addWidget(window.sp_precio_kg, rr, 1)
    rr += 1

    window.lbl_kg = QLabel("KG:")
    gv.addWidget(window.lbl_kg, rr, 0)
    window.sp_kg = QDoubleSpinBox(window, decimals=3, minimum=0.0, maximum=99999999.999)
    window.sp_kg.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
    window.sp_kg.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    window.sp_kg.setEnabled(False)
    gv.addWidget(window.sp_kg, rr, 1)
    rr += 1

    window.lbl_ancho = QLabel("ANCHO:")
    gv.addWidget(window.lbl_ancho, rr, 0)
    window.sp_ancho = QDoubleSpinBox(window, decimals=2, minimum=0.0, maximum=9999.99)
    window.sp_ancho.setValue(0.0)
    window.sp_ancho.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    window.sp_ancho.focusInEvent = lambda event: window.sp_ancho.selectAll()
    window.sp_ancho.editingFinished.connect(window._on_global_dimension_changed)
    gv.addWidget(window.sp_ancho, rr, 1)
    rr += 1

    window.lbl_alto = QLabel("ALTO:")
    gv.addWidget(window.lbl_alto, rr, 0)
    window.sp_alto = QDoubleSpinBox(window, decimals=2, minimum=0.0, maximum=9999.99)
    window.sp_alto.setValue(0.0)
    window.sp_alto.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    window.sp_alto.focusInEvent = lambda event: window.sp_alto.selectAll()
    window.sp_alto.editingFinished.connect(window._on_global_dimension_changed)
    gv.addWidget(window.sp_alto, rr, 1)
    rr += 1

    window.lbl_mo = QLabel("MANO DE OBRA:")
    gv.addWidget(window.lbl_mo, rr, 0)
    window.sp_mo = QDoubleSpinBox(window, decimals=2, minimum=0.0, maximum=99999999.99)
    window.sp_mo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    window.sp_mo.focusInEvent = lambda event: window.sp_mo.selectAll()
    gv.addWidget(window.sp_mo, rr, 1)
    rr += 1

    window.lbl_acc = QLabel("ACCESORIOS:")
    gv.addWidget(window.lbl_acc, rr, 0)
    window.sp_acc = QDoubleSpinBox(window, decimals=2, minimum=0.0, maximum=99999999.99)
    window.sp_acc.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    window.sp_acc.focusInEvent = lambda event: window.sp_acc.selectAll()
    gv.addWidget(window.sp_acc, rr, 1)
    rr += 1

    window.lbl_pu_partida = QLabel("P.U.:")
    gv.addWidget(window.lbl_pu_partida, rr, 0)
    window.sp_pu_partida = QDoubleSpinBox(window, decimals=2, minimum=0.0, maximum=9999999999.99)
    window.sp_pu_partida.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
    window.sp_pu_partida.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    window.sp_pu_partida.setReadOnly(True)
    window.sp_pu_partida.setAlignment(Qt.AlignmentFlag.AlignRight)
    window.sp_pu_partida.setEnabled(False)
    gv.addWidget(window.sp_pu_partida, rr, 1)
    rr += 1

    window.lbl_pzas_global = QLabel("PIEZAS:")
    gv.addWidget(window.lbl_pzas_global, rr, 0)
    window.sb_pzas_global = QSpinBox(window, minimum=1, maximum=999999)
    window.sb_pzas_global.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    window.sb_pzas_global.focusInEvent = lambda event: window.sb_pzas_global.selectAll()
    gv.addWidget(window.sb_pzas_global, rr, 1)
    rr += 1

    lv.addWidget(gb_v)

    gb_r = QGroupBox("Resumen de partida y presupuesto", window)

    def mk_disp():
        w = QDoubleSpinBox(window, decimals=2, minimum=0.0, maximum=9999999999.99)
        w.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        w.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        w.setReadOnly(True)
        w.setAlignment(Qt.AlignmentFlag.AlignRight)
        w.setEnabled(False)
        return w

    gr = QGridLayout(gb_r)
    gr.setContentsMargins(8, 8, 8, 8)
    gr.setSpacing(6)
    rsum = 0

    gr.addWidget(QLabel("TOTAL DE LA PARTIDA:"), rsum, 0)
    window.sp_total_partida = mk_disp()
    gr.addWidget(window.sp_total_partida, rsum, 1)
    rsum += 1

    gr.addWidget(QLabel("SUB TOTAL:"), rsum, 0)
    window.sp_subtotal = mk_disp()
    gr.addWidget(window.sp_subtotal, rsum, 1)
    rsum += 1

    window.lbl_iva = QLabel("I.V.A. (16.00%):")
    gr.addWidget(window.lbl_iva, rsum, 0)
    window.sp_iva = mk_disp()
    gr.addWidget(window.sp_iva, rsum, 1)
    rsum += 1

    gr.addWidget(QLabel("TOTAL:"), rsum, 0)
    window.sp_total = mk_disp()
    gr.addWidget(window.sp_total, rsum, 1)
    rsum += 1

    lv.addWidget(gb_r)
    window.split.addWidget(left)

    # --- PANEL DERECHO (80%) ---
    right = QWidget(window)
    rv = QVBoxLayout(right)
    rv.setContentsMargins(0, 0, 0, 0)
    rv.setSpacing(8)

    bar = QWidget(window)
    b = QGridLayout(bar)
    b.setContentsMargins(0, 0, 0, 0)
    b.setSpacing(6)

    b.addWidget(QLabel("TIPO:"), 0, 0)
    window.cbo_tipo = QComboBox(window)
    window.cbo_tipo.addItems(TIPOS_MATERIAL)
    window.cbo_tipo.currentTextChanged.connect(lambda _=None: window._after_choose_filtro())
    b.addWidget(window.cbo_tipo, 0, 1)
    _connect_upper_combobox(window.cbo_tipo)

    b.addWidget(QLabel("BUSCAR POR:"), 0, 2)
    window.cbo_buscar = QComboBox(window)
    window.cbo_buscar.addItems(TIPOS_BUSQUEDA)
    window.cbo_buscar.currentTextChanged.connect(lambda _=None: window._after_choose_filtro())
    b.addWidget(window.cbo_buscar, 0, 3)
    _connect_upper_combobox(window.cbo_buscar)

    b.addWidget(QLabel("FILTRO:"), 0, 4)
    window.le_filtro = QLineEdit(window)
    window.le_filtro.textChanged.connect(
        lambda _t: (
            window._search_timer.start(),
            window.lst_result.setVisible(bool((window.le_filtro.text() or "").strip()))
        )
    )
    b.addWidget(window.le_filtro, 0, 5)
    _connect_upper_lineedit(window.le_filtro)

    window.lst_result = QListWidget(window)
    window.lst_result.setVisible(False)
    window.lst_result.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    configure_list_widget_for_search_results(window.lst_result)
    window.lst_result.itemClicked.connect(
        lambda it: window._on_pick_result_paquete(it) if window._es_tipo_paquete() else busquedas_module.on_pick_result(window, it)
    )
    window.lst_result.itemActivated.connect(
        lambda it: window._on_pick_result_paquete(it) if window._es_tipo_paquete() else busquedas_module.on_pick_result(window, it)
    )
    b.addWidget(window.lst_result, 1, 0, 1, 6)
    b.setRowStretch(0, 0)
    b.setRowStretch(1, 1)

    rv.addWidget(bar)

    tablas_container = QWidget(window)
    tablas_layout = QVBoxLayout(tablas_container)
    tablas_layout.setContentsMargins(0, 0, 0, 0)
    tablas_layout.setSpacing(4)

    window.gb_tabla_paquetes = QGroupBox("📦 Paquetes", window)
    vm_paquetes = QVBoxLayout(window.gb_tabla_paquetes)
    window.tbl_paquetes = TablaPaquetes(window)
    vm_paquetes.addWidget(window.tbl_paquetes, 1)
    tablas_layout.addWidget(window.gb_tabla_paquetes, 1)

    window.gb_tabla_anidada = QGroupBox("📝 Anidada (Componentes del paquete actual)", window)
    window.gb_tabla_anidada.setVisible(False)
    vm_anidada = QVBoxLayout(window.gb_tabla_anidada)
    window.tbl_anidada = TablaAnidada(window)
    vm_anidada.addWidget(window.tbl_anidada, 1)
    tablas_layout.addWidget(window.gb_tabla_anidada, 1)

    window.gb_tabla_materiales = QGroupBox("📋 Materiales", window)
    vm_materiales = QVBoxLayout(window.gb_tabla_materiales)
    window.tbl = QTableWidget(0, 11, window)
    window.tbl.setHorizontalHeaderLabels([
        "Tipo", "Color", "Clave", "Descripción", "Cant. Ancho",
        "Ancho", "Cant. Alto", "Alto", "Piezas", "P.U.", "Importe"
    ])
    window.tbl.verticalHeader().setVisible(False)
    window.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    window.tbl.itemChanged.connect(
        lambda it: (getattr(window, "_on_tbl_std_changed", None) and window._on_tbl_std_changed(it))
    )
    vm_materiales.addWidget(window.tbl)
    tablas_layout.addWidget(window.gb_tabla_materiales, 1)

    window.gb_tabla_herreria = QGroupBox("🔧 Herrería", window)
    vm_herreria = QVBoxLayout(window.gb_tabla_herreria)
    window.tbl_he = QTableWidget(0, 14, window)
    window.tbl_he.setHorizontalHeaderLabels([
        "Tipo", "Clave", "Descripción", "Cant. Ancho",
        "Ancho", "Cant. Alto", "Alto", "Metros", "Kg/m", "Kgs.", "$/kg",
        "Piezas", "P.U.", "Importe"
    ])
    window.tbl_he.verticalHeader().setVisible(False)
    window.tbl_he.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    window.tbl_he.itemChanged.connect(
        lambda it: (getattr(window, "_on_tbl_he_changed", None) and window._on_tbl_he_changed(it))
    )
    vm_herreria.addWidget(window.tbl_he)
    tablas_layout.addWidget(window.gb_tabla_herreria, 1)

    rv.addWidget(tablas_container, 1)
    window.split.addWidget(right)
    window.setStyleSheet(STYLESHEET)

    QTimer.singleShot(0, lambda: (
        (getattr(window, "_sync_color_rule", None) and window._sync_color_rule(from_user=False)),
        window.le_cliente.setFocus()
    ))
