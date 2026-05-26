import os
import json
from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# Configuración usando variables de entorno (Las que pusiste en Render)
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Brevo (Sendinblue) — envío de correos transaccionales
BREVO_API_KEY   = os.environ.get("BREVO_API_KEY")
SENDER_EMAIL    = os.environ.get("SENDER_EMAIL", "noreply@tudominio.com")
SENDER_NAME     = os.environ.get("SENDER_NAME", "SISTEMA AUT")

def notificar_telegram(nombre, email, empresa, telefono, descripcion=''):
    # Validamos que tengamos las credenciales
    if not TOKEN or not CHAT_ID:
        print("Error: No se han configurado las variables de entorno.")
        return

    empresa_str = f"\n🏢 Empresa: {empresa}" if empresa else ""
    desc_str = f"\n📋 Proyecto: {descripcion}" if descripcion else ""
    mensaje = (
        f"🚀 ¡Nuevo lead!\n"
        f"👤 Nombre: {nombre}\n"
        f"📧 Email: {email}{empresa_str}\n"
        f"📞 Teléfono: {telefono}{desc_str}"
    )
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje}

    try:
        response = requests.post(url, data=payload)
        print("Respuesta de Telegram:", response.text)
    except Exception as e:
        print(f"Error grave al conectar: {e}")

def enviar_correo_confirmacion(nombre, email, empresa, telefono, descripcion):
    """Envía un correo de confirmación al lead usando la API transaccional de Brevo."""
    if not BREVO_API_KEY:
        print("Brevo: BREVO_API_KEY no configurada, se omite el envío de correo.")
        return

    empresa_row = f"""
        <tr>
          <td style="padding:6px 0;color:#777;font-size:13px;letter-spacing:1px;">EMPRESA</td>
          <td style="padding:6px 0;color:#ddd;font-size:13px;">{empresa}</td>
        </tr>""" if empresa else ""

    descripcion_row = f"""
        <tr>
          <td style="padding:6px 0;color:#777;font-size:13px;letter-spacing:1px;">PROYECTO</td>
          <td style="padding:6px 0;color:#ddd;font-size:13px;">{descripcion}</td>
        </tr>""" if descripcion else ""

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#050505;font-family:'Courier New',monospace;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#050505;padding:40px 20px;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0"
             style="background:#0a0a0a;border:1px solid rgba(0,212,255,0.25);max-width:560px;width:100%;">

        <!-- Header -->
        <tr>
          <td style="padding:32px 36px 24px;border-bottom:1px solid rgba(0,212,255,0.12);">
            <p style="margin:0 0 6px;font-size:11px;color:rgba(0,212,255,0.7);letter-spacing:5px;">
              // SISTEMA AUT
            </p>
            <h1 style="margin:0;font-size:22px;color:#00d4ff;letter-spacing:6px;text-transform:uppercase;">
              SOLICITUD RECIBIDA
            </h1>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:28px 36px;">
            <p style="margin:0 0 20px;font-size:14px;color:#bbb;line-height:1.8;">
              Hola <strong style="color:#ddd;">{nombre}</strong>,<br>
              hemos recibido tu solicitud correctamente.<br>
              En las próximas <strong style="color:#00d4ff;">12 horas</strong> nuestra
              asesora te contactará personalmente para guiarte.
            </p>

            <!-- Resumen datos -->
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="border:1px solid rgba(0,212,255,0.12);padding:16px 20px;background:rgba(0,212,255,0.02);">
              <tr>
                <td colspan="2" style="padding-bottom:10px;font-size:10px;color:rgba(0,212,255,0.6);
                    letter-spacing:4px;">RESUMEN DE TU SOLICITUD</td>
              </tr>
              <tr>
                <td style="padding:6px 0;color:#777;font-size:13px;letter-spacing:1px;">NOMBRE</td>
                <td style="padding:6px 0;color:#ddd;font-size:13px;">{nombre}</td>
              </tr>
              <tr>
                <td style="padding:6px 0;color:#777;font-size:13px;letter-spacing:1px;">EMAIL</td>
                <td style="padding:6px 0;color:#ddd;font-size:13px;">{email}</td>
              </tr>
              <tr>
                <td style="padding:6px 0;color:#777;font-size:13px;letter-spacing:1px;">TELÉFONO</td>
                <td style="padding:6px 0;color:#ddd;font-size:13px;">{telefono}</td>
              </tr>
              {empresa_row}
              {descripcion_row}
            </table>

            <p style="margin:24px 0 0;font-size:12px;color:#555;line-height:1.7;">
              Si no realizaste esta solicitud, puedes ignorar este mensaje.
            </p>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:18px 36px;border-top:1px solid rgba(0,212,255,0.08);">
            <p style="margin:0;font-size:10px;color:#333;letter-spacing:3px;">
              SISTEMA AUT &mdash; AUTOMATIZACIÓN INTELIGENTE
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": email, "name": nombre}],
        "subject": "✅ Solicitud recibida — SISTEMA AUT",
        "htmlContent": html_content,
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY,
    }

    try:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers=headers,
            data=json.dumps(payload),
            timeout=10,
        )
        print("Brevo response:", response.status_code, response.text)
    except Exception as e:
        print(f"Error al enviar correo con Brevo: {e}")


@app.route('/')
def inicio():
    return render_template('index.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        empresa = request.form.get('empresa', '').strip()
        telefono = request.form.get('telefono', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        
        # Disparamos la notificación por Telegram
        notificar_telegram(nombre, email, empresa, telefono, descripcion)

        # Enviamos correo de confirmación al lead
        enviar_correo_confirmacion(nombre, email, empresa, telefono, descripcion)
        
        return render_template('registro.html')
    return render_template('index.html')

if __name__ == '__main__':
    # Render asigna el puerto automáticamente, si no, usamos el 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
