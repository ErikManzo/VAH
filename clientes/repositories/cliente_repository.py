# =========================================================
# Archivo: D:\vah\clientes\repositories\cliente_repository.py
# Repositorio de acceso a datos para Clientes (PyODBC optimizado)
# CORREGIDO: campo 'correo' -> 'Email' en TODAS las consultas SQL
# =========================================================

from clientes.models.cliente import Cliente
from clientes.data.db import get_connection
from common.logger_config import get_logger

logger = get_logger("clientes.repositories.cliente_repository")


class ClienteRepository:
    """Repositorio para operaciones CRUD sobre la tabla 'Clientes'."""

    # ================= MÉTODOS PRIVADOS =================
    def _fetchall_dict(self, cursor):
        """Convierte fetchall() en lista de diccionarios."""
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def _fetchone_dict(self, cursor):
        """Convierte fetchone() en diccionario o None."""
        row = cursor.fetchone()
        if not row:
            return None
        columns = [col[0] for col in cursor.description]
        return dict(zip(columns, row))

    # ================= OPERACIONES CRUD =================
    def get_all(self):
        """Devuelve todos los clientes como lista de diccionarios."""
        query = """
        SELECT id, titulo, nombre, a_paterno, a_materno, empresa, direccion,
               num_exterior, num_interior, cp, colonia, municipio, estado,
               rfc, telefono, Email
        FROM Clientes
        ORDER BY nombre
        """
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(query)
                return self._fetchall_dict(cur)
        except Exception:
            logger.exception("Error obteniendo todos los clientes")
            raise

    def get_all_desc(self):
        """Devuelve todos los clientes ordenados por nombre descendente."""
        query = """
        SELECT id, titulo, nombre, a_paterno, a_materno, empresa, direccion,
               num_exterior, num_interior, cp, colonia, municipio, estado,
               rfc, telefono, Email
        FROM Clientes
        ORDER BY nombre DESC
        """
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(query)
                return self._fetchall_dict(cur)
        except Exception:
            logger.exception("Error obteniendo clientes descendentes")
            raise

    def get_by_id(self, cliente_id):
        """Devuelve un cliente por su ID como objeto Cliente."""
        query = """
        SELECT id, titulo, nombre, a_paterno, a_materno, empresa, direccion,
               num_exterior, num_interior, cp, colonia, municipio, estado,
               rfc, telefono, Email
        FROM Clientes
        WHERE id = ?
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, (cliente_id,))
            data = self._fetchone_dict(cur)
            return Cliente(**data) if data else None

    def buscar_por_nombre(self, nombre):
        """Devuelve clientes cuyo nombre comience con el texto dado."""
        query = """
        SELECT id, titulo, nombre, a_paterno, a_materno, empresa, direccion,
               num_exterior, num_interior, cp, colonia, municipio, estado,
               rfc, telefono, Email
        FROM Clientes
        WHERE nombre LIKE ?
        ORDER BY nombre
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, (f"{nombre}%",))
            return self._fetchall_dict(cur)

    def insert(self, cliente: Cliente):
        """Inserta un nuevo cliente y retorna el ID generado."""
        query = """
        INSERT INTO Clientes (titulo, nombre, a_paterno, a_materno, empresa, direccion,
                              num_exterior, num_interior, cp, colonia, municipio, estado,
                              rfc, telefono, Email)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, (
                cliente.titulo, cliente.nombre, cliente.a_paterno, cliente.a_materno,
                cliente.empresa, cliente.direccion, cliente.num_exterior, cliente.num_interior,
                cliente.cp, cliente.colonia, cliente.municipio, cliente.estado,
                cliente.rfc, cliente.telefono, cliente.Email
            ))
            conn.commit()
            cur.execute("SELECT @@IDENTITY")
            row = cur.fetchone()
            return int(row[0]) if row else None

    def update(self, cliente: Cliente):
        """Actualiza un cliente existente."""
        query = """
        UPDATE Clientes
        SET titulo=?, nombre=?, a_paterno=?, a_materno=?, empresa=?, direccion=?,
            num_exterior=?, num_interior=?, cp=?, colonia=?, municipio=?, estado=?,
            rfc=?, telefono=?, Email=?
        WHERE id=?
        """
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, (
                cliente.titulo, cliente.nombre, cliente.a_paterno, cliente.a_materno,
                cliente.empresa, cliente.direccion, cliente.num_exterior, cliente.num_interior,
                cliente.cp, cliente.colonia, cliente.municipio, cliente.estado,
                cliente.rfc, cliente.telefono, cliente.Email, cliente.id
            ))
            conn.commit()
            return True

    def delete(self, cliente_id):
        """Elimina un cliente por su ID."""
        query = "DELETE FROM Clientes WHERE id = ?"
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, (cliente_id,))
            conn.commit()
            return cur.rowcount > 0

    def agrupar_coincidencias_por_id(self, ids):
        """
        Une varios registros en uno solo, priorizando datos no nulos.
        Mantiene el ID más bajo como principal y borra el resto.
        """
        if not ids or len(ids) < 2:
            return False

        ids = sorted(ids)
        id_principal = ids[0]
        ids_a_unir = ids[1:]

        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                f"SELECT * FROM Clientes WHERE id IN ({','.join('?' for _ in ids)})",
                ids
            )
            registros = self._fetchall_dict(cur)

            datos_fusion = {}
            columnas = [c[0] for c in cur.description if c[0] != "id"]
            for col in columnas:
                for reg in registros:
                    if reg.get(col):
                        datos_fusion[col] = reg[col]
                        break

            set_clause = ", ".join(f"{col} = ?" for col in columnas)
            valores = [datos_fusion.get(col) for col in columnas] + [id_principal]
            cur.execute(f"UPDATE Clientes SET {set_clause} WHERE id = ?", valores)

            cur.execute(
                f"DELETE FROM Clientes WHERE id IN ({','.join('?' for _ in ids_a_unir)})",
                ids_a_unir
            )

            conn.commit()
            return True
