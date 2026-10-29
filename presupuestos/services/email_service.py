# -*- coding: utf-8 -*-
import os
import socket
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any
import base64

def _cifrar_contrasena(contrasena: str) -> str:
    """Cifra la contraseña en base64 (mejora mínima de seguridad)"""
    if not contrasena:
        return ""
    return base64.b64encode(contrasena.encode('utf-8')).decode('utf-8')

def _descifrar_contrasena(contrasena_cifrada: str) -> str:
    """Descifra la contraseña desde base64"""
    if not contrasena_cifrada:
        return ""
    try:
        return base64.b64decode(contrasena_cifrada.encode('utf-8')).decode('utf-8')
    except Exception:
        return contrasena_cifrada  # Si falla, retorna tal cual (compatibilidad)

class EmailService:
    def __init__(self, db_service):
        self.db = db_service

    def enviar_correo_presupuesto(self, para: str, asunto: str, mensaje: str, ruta_pdf: str, parametros: Dict[str, Any]) -> tuple:
        remitente = parametros.get('correo_remitente')
        contrasena_raw = parametros.get('contrasena_correo')
        # CORREGIDO: Descifrar contraseña
        contrasena = _descifrar_contrasena(contrasena_raw)
        servidor_smtp = parametros.get('servidor_smtp', 'smtp.office365.com')
        puerto = parametros.get('puerto_smtp', 587)
        if not remitente or not contrasena:
            return False, "No se ha configurado el correo remitente o la contraseña"
        if not os.path.exists(ruta_pdf):
            return False, f"No se encuentra el archivo PDF: {ruta_pdf}"
        try:
            msg = MIMEMultipart()
            msg['From'] = remitente
            msg['To'] = para
            msg['Subject'] = asunto
            msg.attach(MIMEText(mensaje, 'plain', 'utf-8'))
            with open(ruta_pdf, 'rb') as f:
                parte = MIMEBase('application', 'octet-stream')
                parte.set_payload(f.read())
                encoders.encode_base64(parte)
                parte.add_header('Content-Disposition', f'attachment; filename={os.path.basename(ruta_pdf)}')
                msg.attach(parte)
            with smtplib.SMTP(servidor_smtp, puerto, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(remitente, contrasena)
                rechazados = server.send_message(msg)
            if rechazados:
                detalle = ", ".join(f"{dest}: {motivo}" for dest, motivo in rechazados.items())
                return False, f"El servidor SMTP rechazó uno o más destinatarios: {detalle}"
            return True, "Correo aceptado por el servidor SMTP y enviado para entrega"
        except smtplib.SMTPAuthenticationError as e:
            return False, (
                "Error de autenticación SMTP. Verifica correo, contraseña o contraseña de aplicación.\n\n"
                f"Detalle:\n{str(e)}"
            )
        except smtplib.SMTPRecipientsRefused as e:
            return False, f"El servidor rechazó el destinatario.\n\nDetalle:\n{str(e)}"
        except smtplib.SMTPConnectError as e:
            return False, (
                f"No se pudo conectar al servidor SMTP {servidor_smtp}:{puerto}.\n\n"
                f"Detalle:\n{str(e)}"
            )
        except smtplib.SMTPServerDisconnected as e:
            return False, f"El servidor SMTP cerró la conexión inesperadamente.\n\nDetalle:\n{str(e)}"
        except smtplib.SMTPException as e:
            return False, (
                f"Error SMTP durante el envío.\nServidor: {servidor_smtp}:{puerto}\n\n"
                f"Detalle:\n{str(e)}"
            )
        except (socket.timeout, TimeoutError) as e:
            return False, (
                f"Tiempo de espera agotado al conectar con {servidor_smtp}:{puerto}.\n\n"
                f"Detalle:\n{str(e)}"
            )
        except OSError as e:
            return False, (
                f"Error de red o configuración al conectar con {servidor_smtp}:{puerto}.\n\n"
                f"Detalle:\n{str(e)}"
            )
        except Exception as e:
            return False, f"Error inesperado al enviar correo.\n\nDetalle:\n{str(e)}"