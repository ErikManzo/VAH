# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/service_mapi.py
Servicio para enviar correos usando MAPI (cliente de correo predeterminado)
ABRE EL CLIENTE DE CORREO CON EL MENSAJE Y ADJUNTO PREPARADO
"""

from __future__ import annotations
import os
import subprocess
import tempfile
import urllib.parse
from typing import Tuple, Optional


class MapiMailService:
    """
    Servicio que abre el cliente de correo predeterminado de Windows
    con el mensaje y adjunto preparados.
    """

    def enviar_correo(
            self,
            para: str,
            asunto: str,
            mensaje: str,
            ruta_pdf: Optional[str] = None,
            html: bool = True
    ) -> Tuple[bool, str]:
        """
        Abre el cliente de correo predeterminado con el mensaje.
        El usuario debe hacer clic en "Enviar" manualmente.
        """
        try:
            # Para adjuntos, necesitamos usar un archivo .eml temporal
            if ruta_pdf and os.path.exists(ruta_pdf):
                # Crear un archivo .eml temporal
                eml_path = self._crear_eml_con_adjunto(para, asunto, mensaje, ruta_pdf, html)
                if eml_path:
                    # Abrir con el cliente de correo predeterminado
                    os.startfile(eml_path)
                    return True, f"Correo preparado. Se abrirá su cliente de correo.\nRevise y haga clic en Enviar.\n\nArchivo adjunto: {os.path.basename(ruta_pdf)}"

            # Si no hay adjunto, usar mailto
            para_encoded = urllib.parse.quote(para)
            asunto_encoded = urllib.parse.quote(asunto)

            # Limpiar mensaje para mailto (solo texto plano)
            import re
            mensaje_plano = re.sub(r'<[^>]+>', '', mensaje) if html else mensaje
            mensaje_encoded = urllib.parse.quote(mensaje_plano)

            mailto_url = f"mailto:{para_encoded}?subject={asunto_encoded}&body={mensaje_encoded}"
            subprocess.run(['cmd', '/c', 'start', mailto_url], shell=True)

            return True, "Se abrió su cliente de correo. Complete y envíe manualmente."

        except Exception as e:
            return False, f"Error al abrir cliente de correo: {e}"

    def _crear_eml_con_adjunto(self, para: str, asunto: str, mensaje: str, ruta_pdf: str, html: bool = True) -> \
    Optional[str]:
        """Crea un archivo .eml con adjunto usando Outlook Object Model"""
        try:
            import win32com.client
            import pythoncom

            pythoncom.CoInitialize()
            outlook = win32com.client.Dispatch("Outlook.Application")
            mail = outlook.CreateItem(0)

            mail.To = para
            mail.Subject = asunto

            if html:
                mail.HTMLBody = mensaje
            else:
                mail.Body = mensaje

            mail.Attachments.Add(ruta_pdf)

            # Guardar como .eml temporal
            temp_eml = os.path.join(tempfile.gettempdir(), f"presupuesto_{asunto[:20].replace(' ', '_')}.eml")
            mail.SaveAs(temp_eml, 1024)  # 1024 = olMSGUnicode

            return temp_eml

        except Exception as e:
            print(f"Error creando .eml: {e}")
            return None


_mapi_service = None


def get_mapi_service() -> MapiMailService:
    global _mapi_service
    if _mapi_service is None:
        _mapi_service = MapiMailService()
    return _mapi_service