# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/services/presupuesto_repository.py
Repositorio para operaciones de presupuestos en la base de datos.
CORRECCIONES APLICADAS:
SCOPE_IDENTITY() debe consultarse ANTES del commit
CORREGIDO: obtener_presupuesto() construye correctamente cliente_nombre
CORREGIDO: obtener_presupuesto() devuelve descuento_porcentaje
AGREGADO: actualizar_color_global() para persistir color_global en BD
AGREGADO: actualizar_color_items_partida() para recálculo masivo por color
AGREGADO: actualizar_color_partida() para actualizar color_partida en tabla partidas
MODIFICADO: actualizar_color_items_partida() acepta parámetro es_varios
MODIFICADO: _insertar/_actualizar incluyen descuento_porcentaje SOLO si el
caller lo envía (lo que no se envía, no se toca: evita que un
guardado normal resetee el descuento a 0).
Última actualización: 2026
"""
from typing import List, Dict, Any, Optional
from datetime import datetime


class PresupuestoRepository:
    def __init__(self, db_service):
        self.db = db_service

    def guardar_presupuesto(self, datos: dict) -> int:
        if datos.get('id'):
            return self._actualizar(datos)
        return self._insertar(datos)

    def _insertar(self, datos: dict) -> int:
        """
        Inserta un nuevo presupuesto y retorna su ID.
        CORRECCIÓN: Consultar SCOPE_IDENTITY() ANTES del commit
        NUEVO: descuento_porcentaje se incluye solo si viene en datos.
        """
        cols = ["cliente_id", "obra", "presupuesto", "fecha", "color_global"]
        vals = [datos['cliente_id'], datos['obra'], datos['presupuesto'],
                datos['fecha'], datos['color_global']]
        if 'descuento_porcentaje' in datos:
            cols.append("descuento_porcentaje")
            vals.append(datos['descuento_porcentaje'])
        sql = f"""
            INSERT INTO [presupuestos].dbo.presupuestos ({', '.join(cols)})
            VALUES ({', '.join(['?'] * len(cols))})
        """
        with self.db.cursor() as cur:
            cur.execute(sql, vals)
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
                cur.execute("SELECT MAX(id) FROM [presupuestos].dbo.presupuestos")
                max_row = cur.fetchone()
                return int(max_row[0]) if max_row and max_row[0] else 0

    def _actualizar(self, datos: dict) -> int:
        """
        Actualiza un presupuesto existente.
        NUEVO: descuento_porcentaje se incluye en el SET solo si viene en datos.
        """
        set_clausulas = ["cliente_id = ?", "obra = ?", "presupuesto = ?",
                         "fecha = ?", "color_global = ?"]
        vals = [datos['cliente_id'], datos['obra'], datos['presupuesto'],
                datos['fecha'], datos['color_global']]
        if 'descuento_porcentaje' in datos:
            set_clausulas.append("descuento_porcentaje = ?")
            vals.append(datos['descuento_porcentaje'])
        vals.append(datos['id'])
        sql = f"""
            UPDATE [presupuestos].dbo.presupuestos
            SET {', '.join(set_clausulas)}
            WHERE id = ?
        """
        with self.db.cursor() as cur:
            cur.execute(sql, vals)
            cur.commit()
            return datos['id']

    def obtener_presupuesto(self, presupuesto_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un presupuesto completo con datos del cliente.
        CORREGIDO: Construye cliente_nombre usando titulo, nombre, a_paterno, a_materno
        NUEVO: Devuelve descuento_porcentaje (row[6]).
        """
        sql = """
            SELECT p.*, c.titulo, c.nombre, c.a_paterno, c.a_materno
            FROM [presupuestos].dbo.presupuestos p
            JOIN [clientes].dbo.clientes c ON p.cliente_id = c.id
            WHERE p.id = ?
        """
        with self.db.cursor() as cur:
            cur.execute(sql, [presupuesto_id])
            row = cur.fetchone()
            if not row:
                return None
            # CORREGIDO: Construir cliente_nombre con todas las partes disponibles
            # row[10] = titulo, row[11] = nombre, row[12] = a_paterno, row[13] = a_materno
            partes = []
            if row[10]:  # titulo
                partes.append(str(row[10]).strip())
            if row[11]:  # nombre
                partes.append(str(row[11]).strip())
            if row[12]:  # a_paterno
                partes.append(str(row[12]).strip())
            if row[13]:  # a_materno
                partes.append(str(row[13]).strip())
            cliente_nombre = " ".join(partes) if partes else "(SIN NOMBRE)"
            return {
                "id": row[0],
                "cliente_id": row[1],
                "obra": row[2],
                "presupuesto": row[3],
                "fecha": row[4],
                "color_global": row[5],
                "descuento_porcentaje": row[6],
                "cliente_nombre": cliente_nombre
            }

    def obtener_ultimo_numero(self) -> int:
        sql = "SELECT MAX(presupuesto) FROM [presupuestos].dbo.presupuestos"
        with self.db.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()
            return int(row[0]) if row and row[0] is not None else 0

    def listar_presupuestos(self) -> List[Dict[str, Any]]:
        sql = """
            SELECT p.id, p.presupuesto, p.fecha, p.cliente_id, c.titulo, c.nombre, c.a_paterno, c.a_materno
            FROM [presupuestos].dbo.presupuestos p
            JOIN [clientes].dbo.clientes c ON p.cliente_id = c.id
            ORDER BY p.fecha DESC, p.presupuesto DESC
        """
        rows = self.db.fetchall(sql, [])
        out = []
        for r in rows:
            partes = [str(x).strip() for x in [r[4], r[5], r[6], r[7]] if x]
            cliente_nombre = " ".join(partes) or "(SIN NOMBRE)"
            out.append({
                "id": r[0], "presupuesto": r[1], "fecha": r[2],
                "cliente_id": r[3], "cliente_nombre": cliente_nombre,
            })
        return out

    def buscar_presupuestos(self, filtros: Dict[str, Any]) -> List[Dict[str, Any]]:
        condiciones = []
        params = []
        if filtros.get('numero'):
            condiciones.append("p.presupuesto = ?")
            params.append(filtros['numero'])
        if filtros.get('cliente'):
            like = f"%{filtros['cliente']}%"
            condiciones.append("""
                (c.nombre COLLATE Latin1_General_CI_AI LIKE ? OR c.a_paterno COLLATE Latin1_General_CI_AI LIKE ? OR 
                 CONCAT(ISNULL(c.titulo,''),' ',ISNULL(c.nombre,''),' ',ISNULL(c.a_paterno,''),' ',ISNULL(c.a_materno,'')) COLLATE Latin1_General_CI_AI LIKE ?)
            """)
            params.extend([like] * 3)
        if filtros.get('obra'):
            condiciones.append("p.obra COLLATE Latin1_General_CI_AI LIKE ?")
            params.append(f"%{filtros['obra']}%")
        where = " AND ".join(condiciones) if condiciones else "1=1"
        sql = f"""
            SELECT p.id, p.presupuesto, p.fecha, p.obra, p.color_global, c.id, c.titulo, c.nombre, c.a_paterno, c.a_materno
            FROM [presupuestos].dbo.presupuestos p
            JOIN [clientes].dbo.clientes c ON p.cliente_id = c.id
            WHERE {where} ORDER BY p.presupuesto DESC
        """
        rows = self.db.fetchall(sql, params)
        out = []
        for r in rows:
            partes = [str(x).strip() for x in [r[6], r[7], r[8], r[9]] if x]
            out.append({
                "id": r[0], "presupuesto": r[1], "fecha": r[2], "obra": r[3],
                "color_global": r[4], "cliente_id": r[5], "cliente_nombre": " ".join(partes)
            })
        return out

    def actualizar_color_global(self, presupuesto_id: int, nuevo_color: str) -> bool:
        """
        NUEVO: Actualiza el campo color_global en la tabla presupuestos
        mediante UPDATE dirigido (sin tocar el resto de columnas).
        Garantiza que el encabezado del presupuesto quede sincronizado con
        el color usado en el recálculo masivo.
        Args:
            presupuesto_id: ID del presupuesto
            nuevo_color: Color global seleccionado (incluye "VARIOS")
        Returns:
            bool: True si se actualizó correctamente, False en caso de error
        """
        try:
            sql = """
                UPDATE [presupuestos].dbo.presupuestos
                SET color_global = ?
                WHERE id = ?
            """
            with self.db.cursor() as cur:
                cur.execute(sql, (nuevo_color, presupuesto_id))
                cur.commit()
            return True
        except Exception as e:
            print(f"[ERROR] actualizar_color_global: {e}")
            return False

    def actualizar_color_partida(self, partida_id: int, nuevo_color: str, es_varios: bool = False) -> bool:
        """
        Actualiza el campo color_partida en la tabla partidas.
        Args:
            partida_id: ID de la partida
            nuevo_color: Nuevo color a aplicar
            es_varios: Si es True, NO actualiza el color_partida (conserva el actual)
        Returns:
            bool: True si se actualizó correctamente, False en caso de error
        """
        # Si es VARIOS, no actualizar color_partida (conservar el actual)
        if es_varios:
            return True
        try:
            sql = """
                UPDATE [presupuestos].dbo.partidas
                SET color_partida = ?
                WHERE id = ?
            """
            with self.db.cursor() as cur:
                cur.execute(sql, (nuevo_color, partida_id))
                cur.commit()
            return True
        except Exception as e:
            print(f"[ERROR] actualizar_color_partida: {e}")
            return False

    def actualizar_color_items_partida(self, partida_id: int, nuevo_color: str, es_varios: bool = False) -> bool:
        """
        Actualiza el color en todos los items de una partida específica.
        Necesario para el recálculo masivo por color.
        Args:
            partida_id: ID de la partida
            nuevo_color: Nuevo color a aplicar
            es_varios: Si es True, NO actualiza el color (solo retorna True)
        Returns:
            bool: True si se actualizó correctamente, False en caso de error
        """
        # Si es VARIOS, no actualizar el color (cada item mantiene el suyo)
        if es_varios:
            return True
        try:
            sql = """
                UPDATE [presupuestos].dbo.items_partida
                SET color = ?
                WHERE partida_id = ? AND tipo NOT IN ('HERRERIA', 'HERRERÍA')
            """
            with self.db.cursor() as cur:
                cur.execute(sql, (nuevo_color, partida_id))
                cur.commit()
            return True
        except Exception as e:
            print(f"[ERROR] actualizar_color_items_partida: {e}")
            return False

    def obtener_items_partida_con_color(self, partida_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todos los items de una partida con su color actual.
        Útil para verificar el estado antes/después del recálculo.
        """
        sql = """
            SELECT id, tipo, color, clave, descripcion, ca, ancho, ch, alto, piezas, pu, importe,
                   metros, kg_m, kgs, precio_kg
            FROM [presupuestos].dbo.items_partida
            WHERE partida_id = ?
            ORDER BY id
        """
        with self.db.cursor() as cur:
            cur.execute(sql, [partida_id])
            rows = cur.fetchall()
        items = []
        for row in rows:
            items.append({
                "id": row[0],
                "tipo": row[1],
                "color": row[2],
                "clave": row[3],
                "descripcion": row[4],
                "ca": row[5],
                "ancho": row[6],
                "ch": row[7],
                "alto": row[8],
                "piezas": row[9],
                "pu": row[10],
                "importe": row[11],
                "metros": row[12],
                "kg_m": row[13],
                "kgs": row[14],
                "precio_kg": row[15]
            })
        return items