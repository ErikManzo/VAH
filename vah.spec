# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['principal/pantalla_principal.py'],
    pathex=['D:\\vah'],
    binaries=[],
    datas=[
        ('common', 'common'),
        ('clientes', 'clientes'),
        ('proveedores', 'proveedores'),
        ('presupuestos', 'presupuestos'),
        ('cxc', 'cxc'),
        ('concentrador_materiales', 'concentrador_materiales'),
        ('materiales', 'materiales'),
        ('paquetes', 'paquetes'),
        ('principal', 'principal'),
        ('manuales', 'manuales'),
        ('logo_principal.jpg', '.'),
        ('logo.jpg', '.'),
        ('logo.png', '.'),
        ('logo_00001.ico', '.'),
        ('logo_principal_pagina.jpg', '.'),
    ],
    hiddenimports=[
        # Módulos de clientes
        'clientes.art.pantalla_clientes',
        # Módulos de proveedores
        'proveedores.art.pantalla_proveedores',
        # Módulos de presupuestos
        'presupuestos.modulo_presupuestos',
        # Módulos de CXC
        'cxc.art.pantalla_cxc',
        # Módulos de concentrador
        'concentrador_materiales.ui.pantalla_concentrador',
        # Módulos de materiales
        'materiales.aluminio.pantalla_materiales_aluminio',
        'materiales.herreria.pantalla_herreria',
        'materiales.vidrio.pantalla_vidrio',
        'materiales.herrajes.pantalla_herrajes',
        'materiales.plasticos.pantalla_plasticos',
        'materiales.otros.pantalla_otros',
        'materiales.pantalla_catalogo_general',
        # Módulos de paquetes
        'paquetes.aluminio.pantalla_paquete_aluminio',
        'paquetes.herrajes.pantalla_paquete_herrajes',
        'paquetes.herrajes.imprimir',
        # Módulos comunes
        'common.app_paths',
        'common.estilos',
        'common.logger_config',
        'common.focus_simple',
        'common.focus_utils',
        'common.search_utils',
        'common.pdf_utils',
        'common.manuales',
        # Dependencias de terceros
        'pyodbc',
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtPrintSupport',
        'reportlab',
        'pdfplumber',
        'openpyxl',
        'pandas',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyd = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyd,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ERP_VAH',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codepage_utf_8=True,
    icon='logo_00001.ico',
)