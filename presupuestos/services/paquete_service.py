# -*- coding: utf-8 -*-
from typing import List, Dict, Any, Optional

class PaqueteService:
    def __init__(self, db_service, material_service):
        self.db = db_service
        self.materials = material_service

    def _resolve_cols_paquete_al_items(self) -> Dict[str, str]:
        """Detecta los nombres REALES de columnas en aluminio.dbo.paquete_aluminio_items"""
        db = "aluminio"
        table_name = "paquete_aluminio_items"
        sql_cols = f"SELECT COLUMN_NAME FROM [{db}].INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME=?;"
        cols = set(x[0].lower() for x in self.db.fetchall(sql_cols, [table_name]))

        def pick(*cands: str) -> Optional[str]:
            for c in cands:
                if c and c.lower() in cols: return c
            return None

        m = {}
        m["paquete"] = pick("clave_paquete", "clv_paquete", "paquete")
        m["tipo"] = pick("tipo", "tp", "tipo_item")
        m["clave"] = pick("clave", "clv_item", "clv_material", "clv_aluminio", "clv", "clave_item")
        m["horizontal"] = pick("horizontal", "cant_ancho", "h", "hor", "horiz")
        m["vertical"] = pick("vertical", "cant_alto", "v", "ver", "vert")
        m["cantidad"] = pick("cantidad", "cant", "qty", "piezas")
        required = ("paquete", "clave", "cantidad")
        if any(m.get(k) is None for k in required):
            faltantes = [k for k in required if m.get(k) is None]
            raise RuntimeError(f"paquete_aluminio_items: columnas requeridas no encontradas: {', '.join(faltantes)}")
        return {k: v or "" for k, v in m.items()}

    def _resolve_cols_paquete_hr_items(self) -> Dict[str, str]:
        """Detecta los nombres REALES de columnas en herrajes.dbo.paquete_herraje_items"""
        db = "herrajes"
        table_name = "paquete_herraje_items"
        sql_cols = f"SELECT COLUMN_NAME FROM [{db}].INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME=?;"
        cols = set(x[0].lower() for x in self.db.fetchall(sql_cols, [table_name]))

        def pick(*cands: str) -> Optional[str]:
            for c in cands:
                if c and c.lower() in cols: return c
            return None

        m = {}
        m["paquete"] = pick("clave_paquete", "clv_paquete", "paquete")
        m["clave"] = pick("clave", "clv_herraje", "clv_item", "clv_material", "clv", "clave_item")
        m["cantidad"] = pick("cantidad", "cant", "qty", "piezas")
        m["tipo"] = pick("tipo", "tp", "tipo_item")
        required = ("paquete", "clave", "cantidad")
        if any(m.get(k) is None for k in required):
            faltantes = [k for k in required if m.get(k) is None]
            raise RuntimeError(f"paquete_herraje_items: columnas requeridas no encontradas: {', '.join(faltantes)}")
        return {k: v or "" for k, v in m.items()}

    def _buscar_descripcion_material_aluminio(self, clave: str) -> str:
        return self.materials.obtener_descripcion_material("ALUMINIO", clave)

    def _buscar_descripcion_material_herraje(self, clave: str) -> str:
        return self.materials.obtener_descripcion_material("HERRAJES", clave)

    def paquete_aluminio_items(self, clave_paquete: str) -> List[Dict[str, Any]]:
        try:
            cols = self._resolve_cols_paquete_al_items()
            t = "[aluminio].dbo.paquete_aluminio_items"
            sel_parts = []
            sel_parts.append(cols["tipo"] if cols.get("tipo") else "NULL AS tipo")
            sel_parts.append(cols["clave"])
            sel_parts.append(cols["horizontal"] if cols.get("horizontal") else "NULL AS horizontal")
            sel_parts.append(cols["vertical"] if cols.get("vertical") else "NULL AS vertical")
            sel_parts.append(cols["cantidad"])
            sql = f"SELECT {', '.join(sel_parts)} FROM {t} WHERE {cols['paquete']} = ?"
            rows = self.db.fetchall(sql, [clave_paquete])
            if not rows: return []
            out = []
            for r in rows:
                clave = str(r[1]).strip()
                out.append({
                    "tipo": str(r[0]).strip() if r[0] else "ALUMINIO",
                    "clave": clave,
                    "descripcion": self._buscar_descripcion_material_aluminio(clave),
                    "horizontal": float(r[2]) if r[2] is not None else None,
                    "vertical": float(r[3]) if r[3] is not None else None,
                    "cantidad": float(r[4]) if r[4] is not None else 0.0,
                })
            return out
        except Exception as e:
            print(f"Error en paquete_aluminio_items: {e}")
            return []

    def paquete_herrajes_items(self, clave_paquete: str) -> List[Dict[str, Any]]:
        try:
            cols = self._resolve_cols_paquete_hr_items()
            t = "[herrajes].dbo.paquete_herraje_items"
            sel_parts = []
            sel_parts.append(cols["tipo"] if cols.get("tipo") else "'HERRAJES' AS tipo")
            sel_parts.append(cols["clave"])
            sel_parts.append(cols["cantidad"])
            sql = f"SELECT {', '.join(sel_parts)} FROM {t} WHERE {cols['paquete']} = ?"
            rows = self.db.fetchall(sql, [clave_paquete])
            if not rows: return []
            out = []
            for r in rows:
                clave = str(r[1]).strip()
                out.append({
                    "tipo": str(r[0]).strip() if r[0] else "HERRAJES",
                    "clave": clave,
                    "descripcion": self._buscar_descripcion_material_herraje(clave),
                    "horizontal": 0.0, "vertical": 0.0,
                    "cantidad": float(r[2]) if r[2] is not None else 0.0,
                })
            return out
        except Exception as e:
            print(f"Error en paquete_herrajes_items: {e}")
            return []

    def guardar_paquetes_partida(self, partida_id: int, paquetes: List[Dict[str, Any]]):
        with self.db.cursor() as cur:
            cur.execute("DELETE FROM [presupuestos].dbo.partida_paquetes WHERE partida_id = ?", (partida_id,))
            for p in paquetes:
                cur.execute("""
                    INSERT INTO [presupuestos].dbo.partida_paquetes
                    (partida_id, tipo_paquete, clave_paquete, descripcion, ancho, alto, piezas)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (partida_id, p.get('tipo', ''), p.get('clave', ''), p.get('descripcion', ''),
                      p.get('ancho', 0.0), p.get('alto', 0.0), p.get('piezas', 1)))
            cur.commit()

    def obtener_paquetes_partida(self, partida_id: int) -> List[Dict[str, Any]]:
        sql = "SELECT tipo_paquete, clave_paquete, descripcion, ancho, alto, piezas FROM [presupuestos].dbo.partida_paquetes WHERE partida_id = ?"
        rows = self.db.fetchall(sql, [partida_id])
        return [{"tipo": r[0], "clave": r[1], "descripcion": r[2], "ancho": r[3], "alto": r[4], "piezas": r[5]} for r in rows]

    def obtener_paquetes_consolidados(self, presupuesto_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        NUEVO (fuente única de verdad para F5 y relaciones):
        Devuelve los paquetes "EN CONJUNTO" con su número de presupuesto y
        número de partida, sin duplicar datos en ninguna tabla nueva.
        Lee siempre el dato vivo mediante JOIN:
          partida_paquetes -> partidas -> presupuestos.
        Si presupuesto_id es None, devuelve todos los paquetes de todos los
        presupuestos; si se proporciona, solo los de ese presupuesto.
        """
        sql_base = """
            SELECT pr.id, pr.presupuesto, pa.id, pa.partida,
                   pp.tipo_paquete, pp.clave_paquete, pp.descripcion,
                   pp.ancho, pp.alto, pp.piezas
            FROM [presupuestos].dbo.partida_paquetes pp
            JOIN [presupuestos].dbo.partidas pa ON pa.id = pp.partida_id
            JOIN [presupuestos].dbo.presupuestos pr ON pr.id = pa.presupuesto_id
        """
        if presupuesto_id is not None:
            sql = sql_base + " WHERE pr.id = ? ORDER BY pa.partida, pp.id"
            rows = self.db.fetchall(sql, [presupuesto_id])
        else:
            sql = sql_base + " ORDER BY pr.presupuesto, pa.partida, pp.id"
            rows = self.db.fetchall(sql, [])
        return [
            {
                "presupuesto_id": r[0],
                "numero_presupuesto": r[1],
                "partida_id": r[2],
                "numero_partida": r[3],
                "tipo_paquete": r[4],
                "clave_paquete": r[5],
                "descripcion": r[6],
                "ancho": r[7],
                "alto": r[8],
                "piezas": r[9],
            }
            for r in rows
        ]