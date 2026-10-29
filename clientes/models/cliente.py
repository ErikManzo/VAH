# =========================================================
# Archivo: D:\vah\clientes\models\cliente.py
# Descripción: Modelo de datos para Cliente
# CORREGIDO: campo 'correo' ahora se mapea a 'Email' (igual que BD)
# =========================================================
from dataclasses import dataclass
from typing import Optional, List, Any

@dataclass
class Cliente:
    id: Optional[int] = None
    titulo: Optional[str] = None
    nombre: Optional[str] = None
    a_paterno: Optional[str] = None
    a_materno: Optional[str] = None
    empresa: Optional[str] = None
    direccion: Optional[str] = None
    num_exterior: Optional[str] = None
    num_interior: Optional[str] = None
    cp: Optional[str] = None
    colonia: Optional[str] = None
    municipio: Optional[str] = None
    estado: Optional[str] = None
    rfc: Optional[str] = None
    telefono: Optional[str] = None
    Email: Optional[str] = None  # CORREGIDO: antes era 'correo'

    def to_list_with_id(self) -> List[Any]:
        return [
            self.id, self.titulo, self.nombre, self.a_paterno, self.a_materno,
            self.empresa, self.direccion, self.num_exterior, self.num_interior,
            self.cp, self.colonia, self.municipio, self.estado, self.rfc,
            self.telefono, self.Email  # CORREGIDO
        ]

    def to_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "nombre": self.nombre,
            "a_paterno": self.a_paterno,
            "a_materno": self.a_materno,
            "empresa": self.empresa,
            "direccion": self.direccion,
            "num_exterior": self.num_exterior,
            "num_interior": self.num_interior,
            "cp": self.cp,
            "colonia": self.colonia,
            "municipio": self.municipio,
            "estado": self.estado,
            "rfc": self.rfc,
            "telefono": self.telefono,
            "Email": self.Email  # CORREGIDO
        }

#