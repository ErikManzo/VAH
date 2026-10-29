# -*- coding: utf-8 -*-
r"""
D:\vah\tools\load_sql.py

Carga un script SQL (por defecto D:\vah\db\vah.sql) en la base 'vah' de
DESKTOP-AE60PIU\SQLEXPRESS con tolerancia a "líneas de trabajo" (USE …,
SELECT * …, "delete from ;"). Si un lote falla, reintenta por sentencia.
"""

import os, re, sys
from typing import List
import pyodbc
from common.logger_config import get_logger

logger = get_logger("tools.load_sql")

SERVER = r"DESKTOP-AE60PIU\SQLEXPRESS"
DATABASE = "vah"
DEFAULT_SQL_FILE = r"D:\vah\db\vah.sql"

# ---------------- utilidades de conexión ----------------

def available_drivers() -> List[str]:
    installed = [d.strip() for d in pyodbc.drivers()]
    preferred = ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"]
    out = [d for d in preferred if d in installed]
    out += [d for d in installed if ("SQL Server" in d) and (d not in out)]
    return out or ["SQL Server"]

def build_conn_str(driver: str, server: str, database: str) -> str:
    auth = "Trusted_Connection=Yes;"
    if driver == "ODBC Driver 18 for SQL Server":
        extras = "Encrypt=yes;TrustServerCertificate=yes;"
    elif driver == "ODBC Driver 17 for SQL Server":
        extras = "Encrypt=no;"
    else:
        extras = ""
    return f"Driver={{{driver}}};Server={server};Database={database};{auth}{extras}"

def connect_any(server: str, database: str):
    last_err = None
    for drv in available_drivers():
        cs = build_conn_str(drv, server, database)
        try:
            conn = pyodbc.connect(cs, timeout=10)
            conn.autocommit = True
            print(f"[OK] Conectado con: {drv} @ {server} / {database}")
            logger.info("Conectado con driver=%s server=%s database=%s", drv, server, database)
            return conn
        except pyodbc.Error as ex:
            last_err = ex
            print(f"[X] Falló {drv} @ {server}: {ex}")
            logger.warning("Fallo de conexion con driver=%s server=%s: %s", drv, server, ex)
    raise SystemExit(f"No fue posible conectar a {server} (DB={database}). Último error: {last_err}")

def ensure_database(server: str, dbname: str):
    """Crea la BD si falta (sin parámetros en el identificador)."""
    conn = connect_any(server, "master")
    try:
        # saneo soft del nombre (por si acaso)
        safe = re.sub(r"[^A-Za-z0-9_\-]", "_", dbname)
        sql = f"IF DB_ID(N'{safe}') IS NULL CREATE DATABASE [{safe}];"
        cur = conn.cursor()
        cur.execute(sql)
        try:
            conn.commit()
        except Exception:
            pass
        print(f"[OK] Base '{safe}' lista.")
        logger.info("Base %s lista para carga SQL", safe)
    finally:
        conn.close()

# --------------- saneo y partición del SQL ---------------

_re_go = re.compile(r"^[ \t]*GO[ \t]*;?[ \t]*$", re.IGNORECASE | re.MULTILINE)
_re_use = re.compile(r"^[ \t]*USE[ \t]+[\[\]A-Za-z0-9_\\.\-]+[ \t]*;?[ \t]*$", re.IGNORECASE)
_re_select_all = re.compile(r"^[ \t]*SELECT[ \t]+\*[ \t]+FROM[ \t]+", re.IGNORECASE)
_re_bad_delete = re.compile(r"^[ \t]*DELETE[ \t]+FROM[ \t]*;[ \t]*$", re.IGNORECASE)

def sanitize_sql_lines(sql_text: str) -> str:
    """Comenta líneas típicamente problemáticas sin afectar DDL real."""
    out_lines: List[str] = []
    for line in sql_text.splitlines():
        if _re_use.match(line):
            out_lines.append("-- [omitido por loader] " + line); continue
        if _re_select_all.match(line):
            out_lines.append("-- [omitido por loader] " + line); continue
        if _re_bad_delete.match(line):
            out_lines.append("-- [omitido por loader] " + line); continue
        out_lines.append(line)
    return "\n".join(out_lines)

def split_batches(sql_text: str) -> List[str]:
    parts = _re_go.split(sql_text)
    return [p.strip() for p in parts if p.strip()]

def split_statements(batch: str) -> List[str]:
    stmts = [s.strip() for s in batch.split(";") if s.strip()]
    return stmts or ([batch] if batch.strip() else [])

# ------------------- ejecución tolerante -------------------

def execute_batch_or_statements(cur, batch: str, idx: int, total: int):
    try:
        cur.execute(batch)
        try:
            cur.connection.commit()
        except Exception:
            pass
        print(f"  - Lote {idx}/{total} OK")
        logger.debug("Lote SQL %s/%s ejecutado correctamente", idx, total)
        return
    except pyodbc.Error as ex:
        print(f"  ! Lote {idx}/{total} falló, reintentando por sentencia…\n    Motivo: {ex}")
        logger.warning("Lote SQL %s/%s fallo; se reintenta por sentencia: %s", idx, total, ex)
        stmts = split_statements(batch)
        ok = 0; fail = 0
        for s in stmts:
            try:
                cur.execute(s)
                try:
                    cur.connection.commit()
                except Exception:
                    pass
                ok += 1
            except pyodbc.Error as ex2:
                print(f"    - [omitida] {ex2}")
                logger.warning("Sentencia SQL omitida en lote %s/%s: %s", idx, total, ex2)
                fail += 1
        print(f"    Resultado: {ok} OK, {fail} omitidas.")
        logger.info("Resultado lote SQL %s/%s: ok=%s omitidas=%s", idx, total, ok, fail)

def main():
    sql_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SQL_FILE
    if not os.path.isfile(sql_file):
        raise SystemExit(f"No existe el archivo SQL: {sql_file}")

    ensure_database(SERVER, DATABASE)
    conn = connect_any(SERVER, DATABASE)

    with open(sql_file, "r", encoding="utf-8-sig") as f:
        original = f.read()

    sanitized = sanitize_sql_lines(original)
    batches = split_batches(sanitized)
    print(f"[INFO] Ejecutando {len(batches)} lote(s) desde {sql_file} ...")
    logger.info("Ejecutando %s lote(s) desde %s", len(batches), sql_file)

    cur = conn.cursor()
    for idx, batch in enumerate(batches, 1):
        execute_batch_or_statements(cur, batch, idx, len(batches))

    conn.close()
    print("[DONE] Script ejecutado (con saneo). Verifica tablas/columnas creadas.")
    logger.info("Script SQL ejecutado con saneo: %s", sql_file)

if __name__ == "__main__":
    main()
