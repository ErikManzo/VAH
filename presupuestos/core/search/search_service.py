# -*- coding: utf-8 -*-
from typing import List, Dict, Any, Optional

class SearchService:
    def __init__(self, material_service, cliente_service):
        self.materials = material_service
        self.clientes = cliente_service

    def do_material_search(self, tipo: str, buscar_por: str, filtro: str) -> List[Dict[str, Any]]:
        return self.materials.buscar_por_tipo(tipo, buscar_por, filtro)

    def do_cliente_search(self, filtro: str) -> List[Dict[str, Any]]:
        return self.clientes.clientes_buscar(filtro)
