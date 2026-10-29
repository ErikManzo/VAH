# -*- coding: utf-8 -*-
from typing import Optional, Dict

# Constantes de columnas movidas de service.py
COLS_AL_COLOR_MAP = {
    "NATURAL": "nat", "BLANCO": "bco", "E-100": "e100", "E-200": "e200", "E-400": "e400",
    "BRONCE": "bmo", "HUESO": "hue", "GRIS": "gris", "CHOCOLATE": "cho", "N.P.": "np",
    "ACERO": "ace", "MADERA LISA": "madl", "MADERA TEXTURIZADA": "madt"
}

class PricingService:
    def __init__(self, db_service):
        self.db = db_service

    def aluminio_precio(self, clave: str, color: Optional[str]) -> Optional[float]:
        from .database_service import DatabaseService
        # Lógica extraída de service.py:aluminio_precio
        cmap = COLS_AL_COLOR_MAP
        if not color:
            cols = ", ".join(cmap.values())
            sql = f"SELECT {cols} FROM [aluminio].dbo.materiales_aluminio WHERE clave = ?"
            with self.db.cursor() as cur:
                cur.execute(sql, [clave])
                row = cur.fetchone()
                if not row: return None
                for val in row:
                    try:
                        if val is not None and float(val) > 0: return float(val)
                    except: pass
                return None
        
        col = cmap.get((color or "").strip().upper())
        if not col: return None
        sql = f"SELECT {col} FROM [aluminio].dbo.materiales_aluminio WHERE clave = ?"
        with self.db.cursor() as cur:
            cur.execute(sql, [clave])
            row = cur.fetchone()
            return float(row[0]) if row and row[0] is not None else None

    def vidrio_precio(self, clave: str) -> Optional[float]:
        sql = "SELECT precio FROM [vidrio].dbo.materiales_vidrio WHERE clave = ?"
        with self.db.cursor() as cur:
            cur.execute(sql, [clave])
            row = cur.fetchone()
            return float(row[0]) if row and row[0] is not None else None

    def herreria_kg_por_m(self, clave: str) -> Optional[float]:
        sql = "SELECT kilogramos FROM [herreria].dbo.materiales_herreria WHERE clave = ?"
        with self.db.cursor() as cur:
            cur.execute(sql, [clave])
            row = cur.fetchone()
            return float(row[0]) if row and row[0] is not None else None

    def plasticos_precio(self, clave: str) -> Optional[float]:
        sql = "SELECT precio FROM [plasticos].dbo.materiales_plasticos WHERE clave = ?"
        with self.db.cursor() as cur:
            cur.execute(sql, [clave])
            row = cur.fetchone()
            return float(row[0]) if row and row[0] is not None else None

    def otros_precio(self, clave: str) -> Optional[float]:
        sql = "SELECT precio FROM [otros].dbo.materiales_otros WHERE clave = ?"
        with self.db.cursor() as cur:
            cur.execute(sql, [clave])
            row = cur.fetchone()
            return float(row[0]) if row and row[0] is not None else None

    def herrajes_precio(self, clave: str) -> Optional[float]:
        sql = "SELECT precio FROM [herrajes].dbo.materiales_herraje WHERE clave = ?"
        with self.db.cursor() as cur:
            cur.execute(sql, [clave])
            row = cur.fetchone()
            return float(row[0]) if row and row[0] is not None else None

    def aluminio_largo(self, clave: str) -> Optional[float]:
        sql = "SELECT largo FROM [aluminio].dbo.materiales_aluminio WHERE clave = ?"
        row = self.db.fetchone(sql, [clave])
        return float(row[0]) if row and row[0] is not None else None

    def paquete_herrajes_precio_total(self, clave_paquete: str) -> float:
        sql = """
            SELECT SUM(CAST(h.precio AS float) * CAST(i.cantidad AS float)) 
            FROM [herrajes].dbo.paquete_herraje_items i 
            JOIN [herrajes].dbo.materiales_herraje h ON h.clave = i.clv_herraje 
            WHERE i.clave_paquete = ?
        """
        row = self.db.fetchone(sql, [clave_paquete])
        return float(row[0]) if row and row[0] is not None else 0.0

    def try_precio_generico(self, tipo: str, clave: str) -> Optional[float]:
        _GENERIC_MAP = {
            "HERRAJES": ("[herrajes].dbo.materiales_herraje", "precio"),
            "HR": ("[herrajes].dbo.materiales_herraje", "precio"),
            "PLASTICOS": ("[plasticos].dbo.materiales_plasticos", "precio"),
            "PL": ("[plasticos].dbo.materiales_plasticos", "precio"),
            "OTROS": ("[otros].dbo.materiales_otros", "precio"),
            "OT": ("[otros].dbo.materiales_otros", "precio"),
            "VIDRIO": ("[vidrio].dbo.materiales_vidrio", "precio"),
            "VI": ("[vidrio].dbo.materiales_vidrio", "precio"),
        }
        config = _GENERIC_MAP.get(tipo.upper())
        if not config: return None
        table, col = config
        sql = f"SELECT {col} FROM {table} WHERE clave = ?"
        row = self.db.fetchone(sql, [clave])
        return float(row[0]) if row and row[0] is not None else None
