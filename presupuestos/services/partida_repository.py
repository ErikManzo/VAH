# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/services/partida_repository.py
Repositorio para operaciones de partidas en la base de datos.
CORRECCIONES:
1. SCOPE_IDENTITY() se consulta ANTES del commit
2. Manejo de errores para UNIQUE KEY violation
3. Fallback con MAX(id) si SCOPE_IDENTITY() retorna None
"""
from typing import List, Dict, Any, Optional


class PartidaRepository:
    def __init__(self, db_service):
        self.db = db_service

    def guardar_partida(self, datos: dict) -> int:
        if datos.get('id'):
            return self._actualizar(datos)
        return self._insertar(datos)

    def _insertar(self, datos: dict) -> int:
        """
        Inserta una nueva partida y retorna su ID.
        CORRECCIÓN: Consultar SCOPE_IDENTITY() ANTES del commit
        """
        sql = """
            INSERT INTO [presupuestos].dbo.partidas 
            (presupuesto_id, partida, titulo, descripcion, color_partida, 
             desperdicio, fv_porcentaje, kg, ancho, alto, mano_obra, accesorios, 
             piezas, precio_unitario, total_partida)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self.db.cursor() as cur:
            try:
                cur.execute(sql, (
                    datos['presupuesto_id'], 
                    datos.get('partida', 1), 
                    datos.get('titulo', ''),
                    datos.get('descripcion', ''), 
                    datos.get('color_partida'), 
                    datos.get('desperdicio'),
                    datos.get('fv_porcentaje'), 
                    datos.get('kg'), 
                    datos.get('ancho'), 
                    datos.get('alto'),
                    datos.get('mano_obra'), 
                    datos.get('accesorios'), 
                    datos.get('piezas'),
                    datos.get('precio_unitario'), 
                    datos.get('total_partida')
                ))
                
                # CORRECCIÓN: Consultar SCOPE_IDENTITY() ANTES del commit
                cur.execute("SELECT SCOPE_IDENTITY()")
                row = cur.fetchone()
                
                # Hacer commit después de obtener el ID
                cur.commit()
                
                # Manejar el caso donde SCOPE_IDENTITY() retorna None
                if row and row[0] is not None:
                    return int(row[0])
                else:
                    # Fallback: obtener el último ID insertado
                    cur.execute("""
                        SELECT MAX(id) FROM [presupuestos].dbo.partidas 
                        WHERE presupuesto_id = ? AND partida = ?
                    """, (datos['presupuesto_id'], datos.get('partida', 1)))
                    max_row = cur.fetchone()
                    return int(max_row[0]) if max_row and max_row[0] else 0
                    
            except Exception as e:
                # Si hay error de UNIQUE KEY, intentar actualizar en lugar de insertar
                if "UQ_presupuesto_partida" in str(e) or "duplicate key" in str(e).lower():
                    # La partida ya existe, hacer UPDATE
                    return self._actualizar_por_numero(datos)
                raise

    def _actualizar_por_numero(self, datos: dict) -> int:
        """
        Actualiza una partida existente basada en presupuesto_id y número de partida.
        Se usa cuando el INSERT falla por UNIQUE KEY violation.
        """
        sql = """
            UPDATE [presupuestos].dbo.partidas
            SET titulo = ?, descripcion = ?, color_partida = ?, 
                desperdicio = ?, fv_porcentaje = ?, kg = ?, 
                ancho = ?, alto = ?, mano_obra = ?, accesorios = ?, 
                piezas = ?, precio_unitario = ?, total_partida = ?
            WHERE presupuesto_id = ? AND partida = ?
        """
        with self.db.cursor() as cur:
            cur.execute(sql, (
                datos.get('titulo', ''),
                datos.get('descripcion', ''), 
                datos.get('color_partida'), 
                datos.get('desperdicio'),
                datos.get('fv_porcentaje'), 
                datos.get('kg'), 
                datos.get('ancho'), 
                datos.get('alto'),
                datos.get('mano_obra'), 
                datos.get('accesorios'), 
                datos.get('piezas'),
                datos.get('precio_unitario'), 
                datos.get('total_partida'),
                datos['presupuesto_id'],
                datos.get('partida', 1)
            ))
            cur.commit()
            
            # Obtener el ID de la partida actualizada
            cur.execute("""
                SELECT id FROM [presupuestos].dbo.partidas 
                WHERE presupuesto_id = ? AND partida = ?
            """, (datos['presupuesto_id'], datos.get('partida', 1)))
            row = cur.fetchone()
            return int(row[0]) if row and row[0] else 0

    def _actualizar(self, datos: dict) -> int:
        """Actualiza una partida existente por su ID."""
        sql = """
            UPDATE [presupuestos].dbo.partidas
            SET presupuesto_id = ?, partida = ?, titulo = ?, descripcion = ?, 
                color_partida = ?, desperdicio = ?, fv_porcentaje = ?, kg = ?, 
                ancho = ?, alto = ?, mano_obra = ?, accesorios = ?, 
                piezas = ?, precio_unitario = ?, total_partida = ?
            WHERE id = ?
        """
        with self.db.cursor() as cur:
            cur.execute(sql, (
                datos['presupuesto_id'], 
                datos.get('partida', 1), 
                datos.get('titulo', ''),
                datos.get('descripcion', ''), 
                datos.get('color_partida'), 
                datos.get('desperdicio'),
                datos.get('fv_porcentaje'), 
                datos.get('kg'), 
                datos.get('ancho'), 
                datos.get('alto'),
                datos.get('mano_obra'), 
                datos.get('accesorios'), 
                datos.get('piezas'),
                datos.get('precio_unitario'), 
                datos.get('total_partida'), 
                datos['id']
            ))
            cur.commit()
            return datos['id']

    def guardar_items(self, partida_id: int, items: List[Dict[str, Any]]):
        """Guarda los items de una partida (elimina los anteriores y inserta los nuevos)."""
        with self.db.cursor() as cur:
            cur.execute("DELETE FROM [presupuestos].dbo.items_partida WHERE partida_id = ?", (partida_id,))
            if items:
                sql = """
                    INSERT INTO [presupuestos].dbo.items_partida 
                    (partida_id, tipo, color, clave, descripcion, ca, ancho, ch, alto, 
                     piezas, pu, importe, metros, kg_m, kgs, precio_kg)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                for it in items:
                    cur.execute(sql, (
                        partida_id, 
                        it.get('tipo', ''), 
                        it.get('color'), 
                        it.get('clave', ''),
                        it.get('descripcion', ''), 
                        it.get('ca', 1.0), 
                        it.get('ancho', 0.0),
                        it.get('ch', 1.0), 
                        it.get('alto', 0.0), 
                        it.get('piezas', 1),
                        it.get('pu', 0.0), 
                        it.get('importe', 0.0), 
                        it.get('metros'),
                        it.get('kg_m'), 
                        it.get('kgs'), 
                        it.get('precio_kg')
                    ))
            cur.commit()

    def obtener_partidas(self, presupuesto_id: int) -> List[Dict[str, Any]]:
        """Obtiene todas las partidas de un presupuesto."""
        sql = "SELECT * FROM [presupuestos].dbo.partidas WHERE presupuesto_id = ? ORDER BY partida"
        rows = self.db.fetchall(sql, [presupuesto_id])
        # Mapear columnas según la estructura de la BD
        return [dict(zip([col[0] for col in rows[0].cursor_description], r)) for r in rows] if rows else []

    def obtener_items_partida(self, partida_id: int) -> List[Dict[str, Any]]:
        """Obtiene todos los items de una partida."""
        sql = "SELECT * FROM [presupuestos].dbo.items_partida WHERE partida_id = ? ORDER BY id"
        rows = self.db.fetchall(sql, [partida_id])
        return [dict(zip([col[0] for col in rows[0].cursor_description], r)) for r in rows] if rows else []