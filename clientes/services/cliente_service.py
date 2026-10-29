# =========================================================
# Archivo: D:\vah\clientes\services\cliente_service.py
# Servicio de Clientes - Lógica de negocio y acceso a datos
# CORREGIDO: campo 'correo' -> 'Email'
# =========================================================

from clientes.models.cliente import Cliente
from clientes.repositories.cliente_repository import ClienteRepository
from clientes.data.db import get_connection
from common.logger_config import get_logger

logger = get_logger("clientes.services.cliente_service")


class ClienteService:
    """
    Servicio que centraliza la lógica de negocio de Clientes,
    coordinando la comunicación entre la capa de datos (Repository)
    y la capa de presentación (UI).
    """

    def __init__(self):
        self.repo = ClienteRepository()

    # ---------------------------------------------------------
    # Métodos CRUD básicos
    # ---------------------------------------------------------
    def listar_todos(self, como_objetos=False):
        """
        Retorna la lista completa de clientes.
        :param como_objetos: Si True, devuelve lista de objetos Cliente,
                             si False, lista de diccionarios.
        """
        data = self.repo.get_all()
        if como_objetos:
            return [Cliente(**row) for row in data]
        return data

    def obtener_por_id(self, cliente_id):
        """Obtiene un cliente por su ID."""
        return self.repo.get_by_id(cliente_id)

    def listar_todos_desc(self, como_objetos=False):
        """Lista todos los clientes ordenados por nombre descendente."""
        data = self.repo.get_all_desc()
        if como_objetos:
            return [Cliente(**row) for row in data]
        return data

    def buscar_por_nombre(self, nombre, como_objetos=False):
        """Busca clientes cuyo nombre comience con el texto dado."""
        data = self.repo.buscar_por_nombre(nombre)
        if como_objetos:
            return [Cliente(**row) for row in data]
        return data

    def guardar(self, cliente: Cliente):
        """Guarda un nuevo cliente y retorna el ID."""
        # Validación de email (opcional pero debe tener formato correcto si se proporciona)
        if cliente.Email and cliente.Email.strip():
            if "@" not in cliente.Email or "." not in cliente.Email.split("@")[-1]:
                raise ValueError("El email no tiene formato válido")
        return self.repo.insert(cliente)

    def actualizar(self, cliente: Cliente):
        """Actualiza un cliente existente."""
        # Validación de email (opcional pero debe tener formato correcto si se proporciona)
        if cliente.Email and cliente.Email.strip():
            if "@" not in cliente.Email or "." not in cliente.Email.split("@")[-1]:
                raise ValueError("El email no tiene formato válido")
        return self.repo.update(cliente)

    def eliminar(self, cliente_id: int):
        """Elimina un cliente por su ID."""
        return self.repo.delete(cliente_id)

    # ---------------------------------------------------------
    # Método para insertar directamente (legacy)
    # ---------------------------------------------------------
    def insertar(self, cliente: Cliente):
        """
        Inserta un cliente directamente a la BD usando get_connection().
        Retorna el ID generado o None si falla.
        """
        conn = get_connection()
        if conn is None:
            return None

        try:
            cur = conn.cursor()
            query = """
                INSERT INTO Clientes (
                    titulo, nombre, a_paterno, a_materno, empresa, direccion,
                    num_exterior, num_interior, cp, colonia, municipio, estado,
                    rfc, telefono, Email
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """
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
        except Exception as e:
            print(f"[Error insertar] {e}")
            logger.exception("Error insertando cliente legacy")
            return None

    # ---------------------------------------------------------
    # Lógica de negocio: Agrupar coincidencias
    # ---------------------------------------------------------
    def agrupar_coincidencias_por_id(self, ids):
        """
        Consolida varios registros de cliente en uno solo.
        Esta implementación delega la operación al repositorio.
        """
        return self.repo.agrupar_coincidencias_por_id(ids)
