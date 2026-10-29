# -*- coding: utf-8 -*-
"""Script de prueba para verificar SendGrid"""
import sys
import os

# Agregar ruta del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Content, Attachment, FileContent, FileName, FileType, Disposition
    import base64

    print("✅ Librería SendGrid importada correctamente")
except ImportError as e:
    print(f"❌ Error importando SendGrid: {e}")
    sys.exit(1)

# Configuración - REEMPLAZA CON TUS DATOS
API_KEY = "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"
REMITENTE = "vah.ventanasdealuminioyherreria@gmail.com"
DESTINATARIO = "erik.manzo@hotmail.com"  # Cambia esto para probar

print(f"\n📧 Configuración:")
print(f"   API Key: {API_KEY[:20]}...")
print(f"   Remitente: {REMITENTE}")
print(f"   Destinatario: {DESTINATARIO}")

# Crear mensaje
message = Mail(
    from_email=REMITENTE,
    to_emails=DESTINATARIO,
    subject="Prueba de SendGrid - VAH ERP",
    html_content="<h1>Prueba de envío</h1><p>Este es un correo de prueba desde SendGrid.</p>"
)

# Agregar texto plano
plain_text = Content("text/plain", "Este es un correo de prueba desde SendGrid.")
message.add_content(plain_text)

print("\n📤 Enviando correo...")

try:
    sg = SendGridAPIClient(API_KEY)
    response = sg.send(message)

    print(f"\n✅ Respuesta de SendGrid:")
    print(f"   Código de estado: {response.status_code}")
    print(f"   Headers: {response.headers}")
    print(f"   Body: {response.body}")

    if response.status_code in [200, 201, 202]:
        print("\n ¡Correo enviado exitosamente!")
        print("   Revisa la bandeja de entrada del destinatario.")
    else:
        print(f"\n⚠️ SendGrid respondió con código {response.status_code}")
        print(f"   Detalle: {response.body}")

except Exception as e:
    print(f"\n❌ Error al enviar:")
    print(f"   Tipo: {type(e).__name__}")
    print(f"   Mensaje: {str(e)}")

    # Si es error de SendGrid, mostrar detalles
    if hasattr(e, 'body'):
        print(f"   Body: {e.body}")
    if hasattr(e, 'status_code'):
        print(f"   Status Code: {e.status_code}")
    if hasattr(e, 'headers'):
        print(f"   Headers: {e.headers}")