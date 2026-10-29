# -*- coding: utf-8 -*-
"""
GENERADOR MAESTRO DE ANÁLISIS ERP VAH (v4.0)
Secciones 1-10 (v3.0) + nuevas 11-16:
  11 Pipeline de compilación (VIVO vs REDUNDANTE)
  12 Frescura de builds (EXE obsoleto vs fuente)
  13 Mapa de señales -> handlers (presupuestos)
  14 Inventario de purga / código muerto (A/B/C)
  15 Reglas de negocio documentadas
  16 Estado de entornos virtuales
FIX: 4.2 filtra librería estándar; Resumen se genera al final (tablas correctas).
"""
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

import os
import ast
import re
import sys
import pyodbc
from datetime import datetime
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(r"D:\vah")
OUTPUT_DIR = PROJECT_ROOT / "arboles"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "vah_analisis_global_consolidado.txt"
DB_SERVER = r"DESKTOP-AE60PIU\SQLEXPRESS"

EXCLUDE_DIRS = {'build', 'dist', 'cache', 'pycache', '.git', 'node_modules',
                'venv', '.venv', '.venv_aider_312', 'env', '.env', 'logs', 'pdfs',
                'respaldos', 'deprecated', 'arboles', '.vs', '.idea'}
VENV_DIRS = {'.venv', '.venv_aider_312', 'venv', 'env'}
MAIN_MODULES = {'presupuestos', 'clientes', 'proveedores', 'cxc', 'materiales',
                'paquetes', 'concentrador_materiales', 'principal', 'manuales', 'common'}
PIPELINE_VIVO = {'compilar_final.bat', 'recompilar_modulos_onedir.bat',
                 'ejecutar_rapido.bat', 'vah_bd.bat'}
STDLIB = {s.lower() for s in getattr(sys, 'stdlib_module_names', ())}


class AnalizadorMaestroERP:
    def __init__(self):
        self.reporte = []
        self.archivos_python = []
        self.info_archivos = {}
        self.todos_imports = set()
        self.imports_externos = set()
        self.dependencias = defaultdict(set)
        self.dependencias_inversas = defaultdict(set)
        self.funciones_globales = defaultdict(list)
        self.metodos_clase = defaultdict(list)
        self.clases_encontradas = []
        self.tablas_bd = []
        self.docstring_stats = {"clases": {"total": 0, "doc": 0},
                                "funciones": {"total": 0, "doc": 0}}
        self.secrets_found = []
        self.requirements_libs = set()
        self.total_lineas = 0

    # ---------------- helpers ----------------
    def _w(self, t):
        self.reporte.append(t)

    def _sep(self, c="=", n=100):
        self._w(c * n)

    def _es_interno(self, m):
        for mm in MAIN_MODULES:
            if m == mm or m.startswith(f"{mm}."):
                return True
        return (PROJECT_ROOT / m).is_dir()

    def _doc(self, node):
        if not node.body:
            return False
        f = node.body[0]
        return isinstance(f, ast.Expr) and isinstance(f.value, ast.Constant) \
            and isinstance(f.value.value, str)

    def _leer(self, p):
        try:
            return p.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return ""

    # ---------------- 1 estructura ----------------
    def analizar_estructura_y_config(self):
        print("📂 1. Estructura y configuración...")
        self._sep(); self._w("1. ESTRUCTURA DE DIRECTORIOS Y CONFIGURACIÓN"); self._sep(); self._w("")
        self._w("1.1 Archivos de configuración")
        for n in ['requirements.txt', '.env', 'config.json', 'config.py', 'settings.py',
                  'Pipfile', 'pyproject.toml', 'README.md']:
            p = PROJECT_ROOT / n
            if p.is_file():
                self._w(f"  📄 {n} ({p.stat().st_size / 1024:.1f} KB)")
        self._w(""); self._w("1.2 Directorios principales")
        for it in sorted(PROJECT_ROOT.iterdir()):
            if it.is_dir() and not it.name.startswith('.') and it.name not in EXCLUDE_DIRS:
                try:
                    n = len([x for x in it.iterdir() if not x.name.startswith('.')])
                    self._w(f"  📁 {it.name}/  ({n} elementos)")
                except Exception:
                    self._w(f"  📁 {it.name}/  (acceso restringido)")
        self._w(""); self._w("1.3 Recursos UI")
        ui = [f for f in PROJECT_ROOT.rglob("*.ui") if not any(e in f.parts for e in EXCLUDE_DIRS)]
        qrc = [f for f in PROJECT_ROOT.rglob("*.qrc") if not any(e in f.parts for e in EXCLUDE_DIRS)]
        self._w(f"  🖼️  .ui: {len(ui)}   .qrc: {len(qrc)}"); self._w("")

    # ---------------- 2 código ----------------
    def analizar_codigo(self):
        print("💻 2. Código fuente (AST)...")
        self._sep(); self._w("2. ANÁLISIS DE ARQUITECTURA Y CÓDIGO"); self._sep(); self._w("")
        for py in sorted(PROJECT_ROOT.rglob("*.py")):
            if any(e in py.parts for e in EXCLUDE_DIRS) or py.stat().st_size < 100:
                continue
            self.archivos_python.append(py)
        for fp in self.archivos_python:
            content = self._leer(fp)
            rel = str(fp.relative_to(PROJECT_ROOT))
            self.total_lineas += content.count('\n') + 1
            info = {'ruta': rel, 'lineas': content.count('\n') + 1, 'clases': [], 'funciones': []}
            try:
                tree = ast.parse(content, filename=str(fp))
            except SyntaxError:
                self._w(f"  ⚠️ Error de sintaxis en {rel}, omitiendo...")
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for a in node.names:
                        m = a.name.split('.')[0]; self.todos_imports.add(m)
                        if self._es_interno(m):
                            self.dependencias[fp].add(m)
                        else:
                            self.imports_externos.add(m)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    m = node.module.split('.')[0]; self.todos_imports.add(m)
                    if self._es_interno(m):
                        self.dependencias[fp].add(m)
                    else:
                        self.imports_externos.add(m)
                elif isinstance(node, ast.ClassDef):
                    info['clases'].append(node.name)
                    self.clases_encontradas.append({'nombre': node.name, 'ruta': rel})
                    self.docstring_stats["clases"]["total"] += 1
                    if self._doc(node):
                        self.docstring_stats["clases"]["doc"] += 1
                    for it in node.body:
                        if isinstance(it, ast.FunctionDef):
                            if not (it.name.startswith('__') and it.name.endswith('__')):
                                self.metodos_clase[it.name].append(f"{node.name} -> {rel}")
                            self.docstring_stats["funciones"]["total"] += 1
                            if self._doc(it):
                                self.docstring_stats["funciones"]["doc"] += 1
                elif isinstance(node, ast.FunctionDef):
                    info['funciones'].append(node.name)
                    self.funciones_globales[node.name].append(rel)
                    self.docstring_stats["funciones"]["total"] += 1
                    if self._doc(node):
                        self.docstring_stats["funciones"]["doc"] += 1
            for patron in (r'(password|pwd|contrasena|contraseña)\s*=\s*["\']([^"\']+)["\']',
                           r'(api_key|apikey|secret|token)\s*=\s*["\']([^"\']+)["\']'):
                for m in re.finditer(patron, content, re.IGNORECASE):
                    self.secrets_found.append({'archivo': rel,
                                               'linea': content[:m.start()].count('\n') + 1,
                                               'tipo': m.group(1)})
            self.info_archivos[fp] = info
        for mod, deps in self.dependencias.items():
            for d in deps:
                self.dependencias_inversas[d].add(mod)
        self._w("2.1 Estadísticas")
        self._w(f"  📊 Archivos: {len(self.archivos_python)}  |  Líneas: {self.total_lineas:,}  |  Clases: {len(self.clases_encontradas)}")
        self._w("2.2 Métodos duplicados en clases (top 15)")
        c = 0
        for n, ub in self.metodos_clase.items():
            if len(ub) > 1:
                self._w(f"  🔴 {n}() en {len(ub)} clases")
                for u in ub[:4]:
                    self._w(f"       → {u}")
                c += 1
                if c >= 15:
                    break
        self._w("2.3 Funciones globales duplicadas (top 15)")
        c = 0
        for n, ub in self.funciones_globales.items():
            if len(ub) > 1:
                self._w(f"  🔴 {n}() en {len(ub)} archivos")
                c += 1
                if c >= 15:
                    break
        self._w("2.4 Top 10 archivos más grandes")
        for i, info in enumerate(sorted(self.info_archivos.values(), key=lambda x: x['lineas'], reverse=True)[:10], 1):
            self._w(f"  {i}. {info['ruta']} ({info['lineas']:,} líneas)")
        ct, cd = self.docstring_stats["clases"]["total"], self.docstring_stats["clases"]["doc"]
        ft, fd = self.docstring_stats["funciones"]["total"], self.docstring_stats["funciones"]["doc"]
        self._w(f"2.5 Docstrings: clases {cd}/{ct}  |  funciones {fd}/{ft}")
        self._w("2.6 Tecnologías detectadas")
        ui = sorted({l for l in self.todos_imports if 'qt' in l.lower()})
        db = sorted({l for l in self.todos_imports if 'odbc' in l.lower() or 'sql' in l.lower()})
        da = sorted({l for l in self.todos_imports if l.lower() in ('pandas', 'numpy')})
        self._w(f"  UI: {', '.join(ui) or '-'}  |  BD: {', '.join(db) or '-'}  |  Data: {', '.join(da) or '-'}")
        self._w("")

    # ---------------- 3 dependencias ----------------
    def _analizar_dependencias(self):
        print("🔗 3. Dependencias...")
        self._sep(); self._w("3. MAPA DE DEPENDENCIAS"); self._sep(); self._w("")
        self._w("3.1 Módulos más importados")
        for m, c in sorted({m: len(d) for m, d in self.dependencias_inversas.items()}.items(),
                           key=lambda x: x[1], reverse=True)[:10]:
            self._w(f"  📥 {m} → {c}")
        self._w("3.2 Módulos más dependientes")
        for m, c in sorted({m: len(d) for m, d in self.dependencias.items()}.items(),
                           key=lambda x: x[1], reverse=True)[:10]:
            r = str(m.relative_to(PROJECT_ROOT)) if isinstance(m, Path) else str(m)
            self._w(f"  📤 {r} → {c}")
        self._w("3.3 Dependencias circulares")
        circ = []
        mods = list(self.dependencias.keys())
        for i in range(len(mods)):
            for j in range(i + 1, len(mods)):
                a, b = mods[i], mods[j]
                if a in self.dependencias.get(b, set()) and b in self.dependencias.get(a, set()):
                    circ.append((a, b))
        if circ:
            for a, b in circ[:5]:
                self._w(f"  🔄 {a} ↔ {b}")
        else:
            self._w("  ✅ Sin dependencias circulares obvias")
        self._w("")

    # ---------------- 4 requirements (FIX stdlib) ----------------
    def _analizar_requirements(self):
        print("📦 4. Requirements...")
        self._sep(); self._w("4. DEPENDENCIAS EXTERNAS (requirements.txt)"); self._sep(); self._w("")
        req = PROJECT_ROOT / "requirements.txt"
        if not req.exists():
            self._w("  ⚠️ No existe requirements.txt"); self._w("")
            return
        libs = set()
        for line in req.read_text(encoding='utf-8', errors='ignore').splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                m = re.match(r'^([a-zA-Z0-9_\-]+)', line)
                if m:
                    libs.add(m.group(1).lower())
        self.requirements_libs = libs
        ext = {e.lower() for e in self.imports_externos} - STDLIB
        self._w(f"  📦 Listadas en requirements: {len(libs)}")
        self._w("4.1 Instaladas pero NO usadas")
        nu = sorted(libs - ext)
        for l in nu[:10]:
            self._w(f"  ⚠️ {l}")
        if len(nu) > 10:
            self._w(f"  ... y {len(nu) - 10} más")
        if not nu:
            self._w("  ✅ Ninguna")
        self._w("4.2 Usadas pero FALTAN en requirements (filtrada stdlib)")
        fa = sorted(ext - libs)
        for l in fa[:10]:
            self._w(f"  ❌ {l}")
        if len(fa) > 10:
            self._w(f"  ... y {len(fa) - 10} más")
        if not fa:
            self._w("  ✅ Ninguna")
        self._w("")

    # ---------------- 5 seguridad ----------------
    def _analizar_seguridad(self):
        print("🔒 5. Seguridad...")
        self._sep(); self._w("5. SEGURIDAD (secretos hardcodeados)"); self._sep(); self._w("")
        if not self.secrets_found:
            self._w("  ✅ Sin secretos detectados")
        else:
            self._w(f"  🔒 Posibles secretos: {len(self.secrets_found)}")
            for s in self.secrets_found[:10]:
                self._w(f"  ⚠️ {s['archivo']} (línea {s['linea']}) → {s['tipo']}")
        self._w("")

    # ---------------- 6 complejidad ----------------
    def _analizar_complejidad(self):
        print("🧠 6. Complejidad...")
        self._sep(); self._w("6. COMPLEJIDAD CICLOMÁTICA (radon)"); self._sep(); self._w("")
        try:
            from radon.complexity import cc_visit
            alta = []
            for fp in self.archivos_python:
                try:
                    for b in cc_visit(self._leer(fp)):
                        if b.complexity > 10:
                            alta.append((b.name, str(fp.relative_to(PROJECT_ROOT)), b.complexity))
                except Exception:
                    pass
            if alta:
                self._w(f"  🧠 Funciones con complejidad > 10: {len(alta)}")
                for n, r, c in sorted(alta, key=lambda x: x[2], reverse=True)[:10]:
                    self._w(f"  {n}() en {r} → {c}")
            else:
                self._w("  ✅ Sin funciones con complejidad > 10")
        except ImportError:
            self._w("  ⚠️ radon no instalado (pip install radon)")
        self._w("")

    # ---------------- 7 estilo ----------------
    def _analizar_estilo(self):
        print("👔 7. PEP8...")
        self._sep(); self._w("7. ESTILO PEP8 (pycodestyle)"); self._sep(); self._w("")
        try:
            import pycodestyle
            total = 0
            for fp in sorted(self.archivos_python, key=lambda x: x.stat().st_size, reverse=True)[:20]:
                try:
                    ch = pycodestyle.Checker(str(fp), show_pep8=False)
                    for _ in ch.check_all():
                        total += 1
                except Exception:
                    pass
            self._w(f"  👔 Violaciones PEP8 (top 20 archivos por tamaño): {total}")
        except ImportError:
            self._w("  ⚠️ pycodestyle no instalado")
        self._w("")

    # ---------------- 8 BD ----------------
    def analizar_base_de_datos(self):
        print("🗄️ 8. Base de datos...")
        self._sep(); self._w("8. ESTRUCTURA DE BASE DE DATOS"); self._sep(); self._w("")
        try:
            conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_SERVER};Trusted_Connection=yes;')
            cur = conn.cursor()
            cur.execute("SELECT name FROM sys.databases WHERE name NOT IN ('master','tempdb','model','msdb','distribution') ORDER BY name")
            for (db,) in cur.fetchall():
                self._w(f"\n📊 BD: {db}")
                c2 = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_SERVER};DATABASE={db};Trusted_Connection=yes;').cursor()
                c2.execute("""SELECT t.TABLE_NAME, c.COLUMN_NAME, c.DATA_TYPE, c.IS_NULLABLE
                              FROM INFORMATION_SCHEMA.TABLES t
                              JOIN INFORMATION_SCHEMA.COLUMNS c ON t.TABLE_NAME=c.TABLE_NAME
                              WHERE t.TABLE_TYPE='BASE TABLE'
                              ORDER BY t.TABLE_NAME, c.ORDINAL_POSITION""")
                cur_tab = ""
                for t, col, dt, nul in c2.fetchall():
                    if t != cur_tab:
                        self._w(f"  📁 {t}")
                        cur_tab = t
                        self.tablas_bd.append(t)
                    self._w(f"     ├─ {col} ({dt}) [Nulo: {nul}]")
                c2.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS")
                v = [r[0] for r in c2.fetchall()]
                self._w("  👁️ Vistas: " + (", ".join(v) if v else "ninguna"))
                c2.execute("SELECT name FROM sys.objects WHERE type='P'")
                sp = [r[0] for r in c2.fetchall()]
                self._w("  ⚙️ SPs: " + (", ".join(sp) if sp else "ninguno"))
                c2.execute("SELECT name FROM sys.triggers")
                tr = [r[0] for r in c2.fetchall()]
                self._w("  💥 Triggers: " + (", ".join(tr) if tr else "ninguno"))
                c2.close()
            cur.close(); conn.close()
        except Exception as e:
            self._w(f"  ❌ Error BD: {e}")
        self._w("")

    # ---------------- 9 FK ----------------
    def analizar_relaciones_bd(self):
        print("🔗 9. Relaciones BD...")
        self._sep(); self._w("9. RELACIONES ENTRE TABLAS (FK)"); self._sep(); self._w("")
        try:
            conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_SERVER};Trusted_Connection=yes;')
            cur = conn.cursor()
            cur.execute("SELECT name FROM sys.databases WHERE name NOT IN ('master','tempdb','model','msdb','distribution')")
            for (db,) in cur.fetchall():
                c2 = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_SERVER};DATABASE={db};Trusted_Connection=yes;').cursor()
                c2.execute("""SELECT OBJECT_NAME(fk.parent_object_id),
                                     COL_NAME(fkc.parent_object_id, fkc.parent_column_id),
                                     OBJECT_NAME(fk.referenced_object_id),
                                     COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id)
                              FROM sys.foreign_keys fk
                              JOIN sys.foreign_key_columns fkc ON fk.object_id=fkc.constraint_object_id""")
                fks = c2.fetchall()
                self._w(f"📊 {db}:")
                if fks:
                    for f in fks:
                        self._w(f"  🔗 {f[0]}.{f[1]} → {f[2]}.{f[3]}")
                else:
                    self._w("  ℹ️ Sin FKs explícitas (relaciones lógicas en código)")
                c2.close()
            cur.close(); conn.close()
        except Exception as e:
            self._w(f"  ❌ Error FK: {e}")
        self._w("")

    # ---------------- 10 integración ----------------
    def analizar_integracion(self):
        print("🔌 10. Integración BD↔código...")
        self._sep(); self._w("10. INTEGRACIÓN BD ↔ CÓDIGO"); self._sep(); self._w("")
        if not self.tablas_bd:
            self._w("  ⚠️ Sin tablas para comparar"); self._w("")
            return
        refs = defaultdict(list)
        for fp in self.archivos_python:
            low = self._leer(fp).lower()
            for t in self.tablas_bd:
                if t.lower() in low:
                    refs[t].append(fp.name)
        for t in sorted(self.tablas_bd):
            if t in refs:
                self._w(f"  ✓ {t} → {', '.join(sorted(set(refs[t]))[:3])}")
            else:
                self._w(f"  ✗ {t} → (sin referencias en código)")
        self._w("")

    # ---------------- 11 pipeline ----------------
    def _analizar_pipeline(self):
        print("🔧 11. Pipeline...")
        self._sep(); self._w("11. PIPELINE DE COMPILACIÓN Y LANZADORES (VIVO vs REDUNDANTE)"); self._sep(); self._w("")
        for f in sorted(list(PROJECT_ROOT.glob("*.bat")) + list(PROJECT_ROOT.glob("*.ps1"))):
            txt = self._leer(f)
            notas = []
            if '.venv_aider_312' in txt:
                notas.append("env=.venv_aider_312 (FUNCIONAL)")
            elif '.venv\\' in txt or '.venv/' in txt:
                notas.append("env=.venv (posible ROTO)")
            if 'ERP_VAH.spec' in txt:
                notas.append("⚠️ ref. ERP_VAH.spec inexistente")
            if 'vah.spec' in txt:
                notas.append("spec=vah.spec")
            if '--onedir' in txt:
                notas.append("ONEDIR")
            if '--onefile' in txt:
                notas.append("ONEFILE")
            vivo = "✅ VIVO" if f.name in PIPELINE_VIVO else "⚪ REDUNDANTE"
            self._w(f"  {vivo} {f.name} → {'; '.join(notas) or 'sin datos'}")
        self._w("")
        self._w("  RECOMENDACIÓN: pipeline vivo = compilar_final.bat + recompilar_modulos_onedir.bat")
        self._w("")

    # ---------------- 12 frescura ----------------
    def _analizar_frescura_builds(self):
        print("🕐 12. Frescura de builds...")
        self._sep(); self._w("12. FRESCURA DE BUILDS (EXE vs fuente)"); self._sep(); self._w("")
        src_max = max((f.stat().st_mtime for f in self.archivos_python), default=0)
        if src_max:
            self._w(f"  📄 Fuente más reciente: {datetime.fromtimestamp(src_max):%Y-%m-%d %H:%M}")
        for exe in sorted(PROJECT_ROOT.rglob("*.exe")):
            if any(e in exe.parts for e in VENV_DIRS):
                continue
            mt = exe.stat().st_mtime
            tag = "❌ OBSOLETO" if mt < src_max else "✅ al día"
            self._w(f"  {tag} {exe.relative_to(PROJECT_ROOT)} ({datetime.fromtimestamp(mt):%Y-%m-%d %H:%M})")
        self._w("")

    # ---------------- 13 señales ----------------
    def _analizar_senales(self):
        print("📡 13. Señales→handlers...")
        self._sep(); self._w("13. MAPA DE SEÑALES → HANDLERS (presupuestos)"); self._sep(); self._w("")
        pat = re.compile(r"([\w.]+)\.(currentTextChanged|valueChanged|textChanged|textEdited|"
                         r"itemChanged|clicked|activated|editingFinished|doubleClicked|"
                         r"itemClicked|itemActivated|returnPressed)\.connect\(([^)\n]*)\)")
        total = 0
        for py in sorted((PROJECT_ROOT / "presupuestos").rglob("*.py")):
            if any(e in py.parts for e in EXCLUDE_DIRS):
                continue
            content = self._leer(py)
            hits = pat.findall(content)
            if hits:
                self._w(f"  📄 {py.relative_to(PROJECT_ROOT)}")
                for w, s, h in hits[:15]:
                    self._w(f"     {w}.{s} → {h.strip()[:60]}")
                    total += 1
        self._w(f"\n  Total conexiones detectadas: {total}")
        self._w("")

    # ---------------- 14 purga ----------------
    def _analizar_purga(self):
        print("🗑️ 14. Inventario de purga...")
        self._sep(); self._w("14. INVENTARIO DE PURGA / CÓDIGO MUERTO (A/B/C)"); self._sep(); self._w("")
        self._w("  [A] ELIMINAR_SEGURO:")
        for a in ["**/__pycache__/**", "**/*.pyc", ".pytest_cache/**", ".aider.*", "build/**",
                  "logs/*.log", "aluminio_db.log", "parse_pdf.log", "resultado compilación.txt",
                  "audit_*.txt", "estructura_completa.txt", "archivos_python.txt", "todos_archivos.txt",
                  "dist/modulos_temp/**", "dist/ERP_VAH.exe (raíz)"]:
            self._w(f"     - {a}")
        self._w("  [B] MOVER_A_RESPALDO:")
        for b in ["deprecated/**", "respaldos/**", "**/*.bak", "**/*.bak2", "**/*.bak3",
                  "diagnostico_clases.py", "explorar_datos.py", "explorar_modulos_con_datos.py",
                  "explorar_vah.py", "fix_db_name.py", "identificar_bd.py", "test_conexion.py",
                  "test_erp.py", "test_xiyan.py", "importar_paquetes_herrajes.py"]:
            self._w(f"     - {b}")
        self._w("  [C] REVISAR_HUMANO:")
        for c in ["erp_manager.py", "servidor_sql.py", "run_presupuestos.py", "logo.svg",
                  "cache/**", "pdfs/**", "vah.spec.backup", "dist/modulos_onedir/**", "tools/**",
                  "scripts/**", "soporteria/**", "tests/smoke_test_erp.py", "db/_snapshots/**", "logs/*.csv"]:
            self._w(f"     - {c}")
        self._w("")

    # ---------------- 15 reglas ----------------
    def _analizar_reglas_negocio(self):
        print("📐 15. Reglas de negocio...")
        self._sep(); self._w("15. REGLAS DE NEGOCIO DOCUMENTADAS (referencias en código)"); self._sep(); self._w("")
        reglas = [
            ("Color global VARIOS vs específico", r"VARIOS"),
            ("Margen de corte aluminio (largo-0.10)", r"MARGEN_CORTE|largo\s*-\s*0\.10"),
            ("Ajuste industrial (múltiplo 0.05)", r"adjust_dimension|round_up_to_005"),
            ("Dispatch central de cálculo", r"dispatch_calculo"),
            ("Regla precio cero (guard)", r"guard_before_add"),
            ("Resumen: D=C*(1+desp), E=D*(1+FV), Total=E*piezas", r"sb_desperdicio|sb_fv_pct|sb_pzas_global"),
        ]
        for nombre, patron in reglas:
            self._w(f"  📌 {nombre}")
            rx = re.compile(patron)
            hits = 0
            for py in sorted((PROJECT_ROOT / "presupuestos").rglob("*.py")):
                if any(e in py.parts for e in EXCLUDE_DIRS):
                    continue
                content = self._leer(py)
                for m in rx.finditer(content):
                    self._w(f"     → {py.relative_to(PROJECT_ROOT)}:{content[:m.start()].count(chr(10)) + 1}")
                    hits += 1
                    if hits >= 4:
                        break
                if hits >= 4:
                    break
            if hits == 0:
                self._w("     → (sin referencias)")
        self._w("")

    # ---------------- 16 entornos ----------------
    def _analizar_entornos(self):
        print("🐍 16. Entornos virtuales...")
        self._sep(); self._w("16. ESTADO DE ENTORNOS VIRTUALES"); self._sep(); self._w("")
        for v in ('.venv', '.venv_aider_312'):
            cfg = PROJECT_ROOT / v / "pyvenv.cfg"
            if not cfg.exists():
                self._w(f"  ⚠️ {v}: no existe")
                continue
            txt = self._leer(cfg)
            exe = re.search(r'executable\s*=\s*(.+)', txt)
            ver = re.search(r'version\s*=\s*(.+)', txt)
            ok = Path(exe.group(1).strip()).exists() if exe else False
            self._w(f"  {'✅ FUNCIONAL' if ok else '❌ ROTO'} {v} → Python {ver.group(1).strip() if ver else '?'}")
        self._w("")
        self._w("  RECOMENDACIÓN: migrar lanzar_erp.bat y lanzar_presupuestos.bat a .venv_aider_312")
        self._w("")

    # ---------------- resumen (al final, con todos los datos) ----------------
    def _generar_resumen(self):
        r = []
        r.append("=" * 100)
        r.append("📊 RESUMEN EJECUTIVO")
        r.append("=" * 100)
        r.append("")
        r.append(f"  ├─ Archivos Python analizados: {len(self.archivos_python)}")
        r.append(f"  ├─ Líneas de código: {self.total_lineas:,}")
        r.append(f"  ├─ Clases: {len(self.clases_encontradas)}")
        r.append(f"  ├─ Funciones globales duplicadas: {len([k for k, v in self.funciones_globales.items() if len(v) > 1])}")
        r.append(f"  ├─ Métodos duplicados: {len([k for k, v in self.metodos_clase.items() if len(v) > 1])}")
        r.append(f"  ├─ Archivos críticos (>2000 líneas): {len([i for i in self.info_archivos.values() if i['lineas'] > 2000])}")
        r.append(f"  ├─ Tablas en Base de Datos: {len(self.tablas_bd)}")
        r.append(f"  └─ Dependencias en requirements: {len(self.requirements_libs)}")
        r.append("")
        r.append("=" * 100)
        r.append("")
        return r

    # ---------------- orquestador ----------------
    def generar_reporte(self):
        self.analizar_estructura_y_config()   # 1
        self.analizar_codigo()                # 2
        self._analizar_dependencias()         # 3
        self._analizar_requirements()         # 4
        self._analizar_seguridad()            # 5
        self._analizar_complejidad()          # 6
        self._analizar_estilo()               # 7
        self.analizar_base_de_datos()         # 8
        self.analizar_relaciones_bd()         # 9
        self.analizar_integracion()           # 10
        self._analizar_pipeline()             # 11
        self._analizar_frescura_builds()      # 12
        self._analizar_senales()              # 13
        self._analizar_purga()                # 14
        self._analizar_reglas_negocio()       # 15
        self._analizar_entornos()             # 16
        final = self._generar_resumen() + self.reporte
        final += ["", "=" * 100, "FIN DEL ANÁLISIS CONSOLIDADO",
                  "Generado por: generador_gral_arbol_txt.py (v4.0)", "=" * 100]
        OUTPUT_FILE.write_text("\n".join(final), encoding="utf-8")
        print(f"\n✅ Generado: {OUTPUT_FILE} ({OUTPUT_FILE.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=" * 70)
    print("GENERADOR MAESTRO DE ANÁLISIS ERP VAH (v4.0)")
    print("=" * 70)
    AnalizadorMaestroERP().generar_reporte()
    print("PROCESO COMPLETADO")