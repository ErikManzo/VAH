# -*- coding: utf-8 -*-
"""
Diagnóstico de tipos de paquete existentes en la base de datos.

Se ejecuta automáticamente al inicio de cada corrida de concentración.
Registra los valores reales de tipo_paquete encontrados.
"""

from typing import List, Dict, Any
from concentrador_materiales.services.logger_config import registrar_info, registrar_advertencia


class DiagnosticoPaquetes:
    """
    Diagnóstico para detectar tipos de paquete en la base de datos.
    """

    def __init__(self, concentrador_repo):
        """
        Inicializa el diagnóstico.

        Args:
            concentrador_repo: Repositorio concentrador para consultas
        """
        self.concentrador_repo = concentrador_repo
        self.tipos_encontrados: List[str] = []
        self.advertencias: List[str] = []

    def ejecutar_diagnostico(self) -> Dict[str, Any]:
        """
        Ejecuta el diagnóstico de tipos de paquete.

        Returns:
            Dict con resultados del diagnóstico
        """
        registrar_info("DIAGNOSTICO_INICIO", "Iniciando diagnóstico de tipos de paquete")

        try:
            # Obtener tipos de paquete desde la BD
            tipos = self._obtener_tipos_paquete_existentes()
            self.tipos_encontrados = tipos

            registrar_info(
                "TIPOS_PAQUETE_ENCONTRADOS",
                f"Tipos encontrados: {tipos if tipos else 'ninguno'}",
                {"tipos": tipos}
            )

            # Validar tipos conocidos
            tipos_conocidos = {"ALUMINIO", "HERRAJES"}

            for tipo in tipos:
                tipo_upper = tipo.strip().upper()
                if tipo_upper not in tipos_conocidos:
                    advertencia = f"Tipo de paquete desconocido encontrado: '{tipo_upper}'"
                    self.advertencias.append(advertencia)
                    registrar_advertencia(
                        "TIPO_PAQUETE_DESCONOCIDO",
                        advertencia,
                        {"tipo": tipo}
                    )

            registrar_info(
                "DIAGNOSTICO_FIN",
                f"Diagnóstico completado. {len(self.advertencias)} advertencias.",
                {"total_tipos": len(tipos), "advertencias": len(self.advertencias)}
            )

            return {
                "tipos_encontrados": self.tipos_encontrados,
                "advertencias": self.advertencias,
                "total_tipos": len(self.tipos_encontrados),
                "total_advertencias": len(self.advertencias)
            }

        except Exception as e:
            error_msg = f"Error durante diagnóstico de paquetes: {str(e)}"
            registrar_advertencia("DIAGNOSTICO_ERROR", error_msg, {})
            return {
                "tipos_encontrados": [],
                "advertencias": [error_msg],
                "error": str(e)
            }

    def _obtener_tipos_paquete_existentes(self) -> List[str]:
        """
        Obtiene los valores DISTINCT de tipo_paquete desde partida_paquetes.

        Returns:
            Lista de tipos encontrados
        """
        # Método directo usando consulta SQL
        cursor = None
        connection = None
        try:
            from db.conn import get_connection
            connection = get_connection()
            cursor = connection.cursor()

            query = """
                SELECT DISTINCT 
                    tipo_paquete
                FROM presupuestos.dbo.partida_paquetes
                WHERE tipo_paquete IS NOT NULL
                ORDER BY tipo_paquete
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            tipos = [row[0].strip() for row in rows if row[0]]
            return tipos

        except Exception as e:
            registrar_advertencia(
                "CONSULTA_TIPOS_PAQUETE_ERROR",
                f"No se pudieron obtener tipos de paquete: {str(e)}",
                {}
            )
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                try:
                    connection.close()
                except Exception:
                    pass

    def obtener_resumen(self) -> str:
        """
        Retorna un resumen textual del diagnóstico.
        """
        if not self.tipos_encontrados:
            return "No se encontraron paquetes en la base de datos."

        resumen = f"Tipos de paquete encontrados ({len(self.tipos_encontrados)}):\n"
        for tipo in self.tipos_encontrados:
            resumen += f"  - {tipo}\n"

        if self.advertencias:
            resumen += f"\nAdvertencias ({len(self.advertencias)}):\n"
            for adv in self.advertencias:
                resumen += f"  ⚠ {adv}\n"

        return resumen