# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['principal\\pantalla_principal.py'],
    pathex=[],
    binaries=[],
    datas=[('common', 'common'), ('presupuestos', 'presupuestos'), ('clientes', 'clientes'), ('proveedores', 'proveedores'), ('cxc', 'cxc'), ('concentrador_materiales', 'concentrador_materiales'), ('materiales', 'materiales'), ('paquetes', 'paquetes'), ('db', 'db'), ('manuales', 'manuales'), ('pdfs', 'pdfs')],
    hiddenimports=['PyQt6', 'pyodbc', 'pandas', 'numpy'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ERP_VAH',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['logo_00001.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ERP_VAH',
)
