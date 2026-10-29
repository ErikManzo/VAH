# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/service_outlook.py
Servicio para enviar correos usando Outlook Desktop (win32com)
CON VERSIÓN ALTERNATIVA QUE USA EL BUZÓN DE SALIDA (Outbox)
"""

from __future__ import annotations
import os
import time
from typing import Tuple, Optional


class OutlookMailService:
    """
    Servicio para enviar correos electrónicos usando Microsoft Outlook.
    Utiliza la API COM de Outlook (win32com).
    """

    def __init__(self):
        self._outlook = None
        self._disponible = None

    def _inicializar_outlook(self) -> bool:
        """Inicializa la conexión con Outlook."""
        try:
            import win32com.client as win32
            from win32com.client import Dispatch
            import pythoncom

            pythoncom.CoInitialize()

            # Intentar obtener Outlook existente
            try:
                self._outlook = win32.GetActiveObject("Outlook.Application")
            except:
                self._outlook = Dispatch("Outlook.Application")

            if self._outlook is None:
                self._disponible = False
                return False

            self._disponible = True
            return True

        except ImportError:
            self._disponible = False
            return False
        except Exception as e:
            self._disponible = False
            return False

    def esta_disponible(self) -> bool:
        if self._disponible is None:
            self._inicializar_outlook()
        return self._disponible and self._outlook is not None

    def enviar_correo(
            self,
            para: str,
            asunto: str,
            mensaje: str,
            ruta_pdf: Optional[str] = None,
            html: bool = True
    ) -> Tuple[bool, str]:
        """
        Envía un correo usando Outlook.
        Versión que crea el correo y lo deja en la bandeja de salida.
        """
        if not self.esta_disponible():
            return False, "Outlook no está disponible"

        try:
            import pythoncom
            pythoncom.CoInitialize()

            # Crear correo
            mail = self._outlook.CreateItem(0)

            mail.To = para
            mail.Subject = asunto

            if html:
                mail.HTMLBody = mensaje
            else:
                mail.Body = mensaje

            if ruta_pdf and os.path.exists(ruta_pdf):
                mail.Attachments.Add(ruta_pdf)

            # Enviar
            mail.Send()

            return True, "Correo enviado exitosamente"

        except Exception as e:
            return False, f"Error: {str(e)}"


_outlook_service = None


def get_outlook_service() -> OutlookMailService:
    global _outlook_service
    if _outlook_service is None:
        _outlook_service = OutlookMailService()
    return _outlook_service