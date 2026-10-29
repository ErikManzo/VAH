# -*- coding: utf-8 -*-
from typing import List, Dict, Any

class ClienteService:
    def __init__(self, db_service):
        self.db = db_service

    def clientes_buscar(self, filtro: str) -> List[Dict[str, Any]]:
        text = (filtro or "").strip()
        if not text: return []
        like = f"%{text}%"
        
        sql = """
            SELECT TOP (80) id, titulo, nombre, a_paterno, a_materno
            FROM [clientes].dbo.clientes 
            WHERE CONCAT(ISNULL(titulo,''),' ',ISNULL(nombre,''),' ',ISNULL(a_paterno,''),' ',ISNULL(a_materno,'')) COLLATE Latin1_General_CI_AI LIKE ?
            OR titulo COLLATE Latin1_General_CI_AI LIKE ?
            OR nombre COLLATE Latin1_General_CI_AI LIKE ?
            OR a_paterno COLLATE Latin1_General_CI_AI LIKE ?
            OR a_materno COLLATE Latin1_General_CI_AI LIKE ?
            ORDER BY nombre, a_paterno
        """
        
        with self.db.cursor() as cur:
            cur.execute(sql, [like] * 5)
            rows = cur.fetchall()
            out = []
            for r in rows:
                cliente = {
                    "id": r[0],
                    "titulo": r[1], "nombre": r[2], "a_paterno": r[3], "a_materno": r[4]
                }
                partes = [str(x).strip() for x in [r[1], r[2], r[3], r[4]] if x]
                cliente["display"] = " ".join(partes) or "(SIN NOMBRE)"
                out.append(cliente)
            return out
