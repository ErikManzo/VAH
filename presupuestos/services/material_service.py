# -*- coding: utf-8 -*-
from typing import List, Dict, Any, Optional

class MaterialService:
    def __init__(self, db_service):
        self.db = db_service

    def buscar_por_tipo(self, tipo: str, buscar_por: str, filtro: str) -> List[Dict[str, Any]]:
        # Mapeo de tablas movido de service.py
        _TABLES = {
            "ALUMINIO": "[aluminio].dbo.materiales_aluminio",
            "PAQUETE ALUMINIO": "[aluminio].dbo.paquetes_aluminio",
            "HERRERIA": "[herreria].dbo.materiales_herreria",
            "HERRERÍA": "[herreria].dbo.materiales_herreria",
            "VIDRIO": "[vidrio].dbo.materiales_vidrio",
            "PLASTICOS": "[plasticos].dbo.materiales_plasticos",
            "PLÁSTICOS": "[plasticos].dbo.materiales_plasticos",
            "HERRAJES": "[herrajes].dbo.materiales_herraje",
            "PAQUETE HERRAJES": "[herrajes].dbo.paquetes_herrajes",
            "OTROS": "[otros].dbo.materiales_otros",
        }
        
        tabla = _TABLES.get(tipo.upper())
        if not tabla: return []
        return self.buscar_por_tabla(tabla=tabla, buscar_por=buscar_por, filtro=filtro)

    def buscar_por_tabla(self, tabla: str, buscar_por: str, filtro: str, database: str = None, top: int = 100) -> List[Dict[str, Any]]:
        if database:
            tabla_full = f"[{database}].dbo.{tabla}" if "." not in tabla else tabla
        else:
            tabla_full = tabla

        like_pattern = f"%{filtro}%"
        
        sql = f"""
            SELECT TOP ({int(top)}) clave, descripcion 
            FROM {tabla_full} 
            WHERE (
                clave COLLATE Latin1_General_CI_AI LIKE ?
                OR descripcion COLLATE Latin1_General_CI_AI LIKE ?
            )
            ORDER BY clave, descripcion
        """
        
        rows = self.db.fetchall(sql, [like_pattern, like_pattern])
        return [{"clave": str(r[0]).strip(), "descripcion": str(r[1]).strip()} for r in rows]

    def obtener_descripcion_material(self, tipo: str, clave: str) -> str:
        return self._buscar_descripcion_material_generico(tipo, clave)

    def _buscar_descripcion_material_generico(self, tipo: str, clave: str) -> str:
        _TABLES = {
            "ALUMINIO": "[aluminio].dbo.materiales_aluminio",
            "HERRAJES": "[herrajes].dbo.materiales_herraje",
            "VIDRIO": "[vidrio].dbo.materiales_vidrio",
            "HERRERIA": "[herreria].dbo.materiales_herreria",
            "HERRERÍA": "[herreria].dbo.materiales_herreria",
            "PLASTICOS": "[plasticos].dbo.materiales_plasticos",
            "PLÁSTICOS": "[plasticos].dbo.materiales_plasticos",
            "OTROS": "[otros].dbo.materiales_otros",
        }
        tabla = _TABLES.get(tipo.upper())
        if not tabla: return f"Material {clave}"
        
        sql = f"SELECT descripcion FROM {tabla} WHERE clave = ?"
        row = self.db.fetchone(sql, [clave])
        return str(row[0]).strip() if row and row[0] else f"Material {clave}"
