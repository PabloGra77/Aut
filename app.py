import os
import json
from flask import Flask, render_template, request
import requests
try:
    from dotenv import load_dotenv
    load_dotenv()  # Solo activo en desarrollo local si python-dotenv está instalado
except ImportError:
    pass

app = Flask(__name__)

# ── Verificación de configuración al arrancar ───────────────────────────────
TOKEN        = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID      = os.environ.get("TELEGRAM_CHAT_ID")
BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
SENDER_EMAIL  = os.environ.get("SENDER_EMAIL", "noreply@tudominio.com")
SENDER_NAME   = os.environ.get("SENDER_NAME", "SISTEMA AUT")

print("[CONFIG] TELEGRAM_TOKEN   :", "OK" if TOKEN        else "⚠ NO CONFIGURADO")
print("[CONFIG] TELEGRAM_CHAT_ID :", "OK" if CHAT_ID      else "⚠ NO CONFIGURADO")
print("[CONFIG] BREVO_API_KEY    :", "OK" if BREVO_API_KEY else "⚠ NO CONFIGURADO")
print("[CONFIG] SENDER_EMAIL     :", SENDER_EMAIL)

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

def enviar_sms_confirmacion(nombre, telefono):
    """Envía un SMS de confirmación al lead usando la API transaccional de Brevo."""
    if not BREVO_API_KEY:
        print("Brevo SMS: BREVO_API_KEY no configurada, se omite el envío de SMS.")
        return

    # Limpiar número a formato E.164: quitar espacios, guiones y paréntesis
    telefono_limpio = (
        telefono.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    )
    if not telefono_limpio.startswith('+'):
        print(f"[BREVO SMS] ⚠ Número sin código de país, se omite: {telefono_limpio}")
        return

    # Sin emojis para garantizar codificacion GSM-7 (160 chars por segmento)
    nombre_ascii = nombre[:20]  # Evitar nombres muy largos que corten el mensaje
    mensaje = (
        f"Hola {nombre_ascii}, tu solicitud fue recibida por SISTEMA AUT. "
        f"Te contactaremos en las proximas 12 horas."
    )[:160]

    payload = {
        "sender": "SISTAUT",
        "recipient": telefono_limpio,
        "content": mensaje,
        "type": "transactional",
        "unicode": False,
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY,
    }

    try:
        response = requests.post(
            "https://api.brevo.com/v3/transactionalSMS/sms",
            headers=headers,
            data=json.dumps(payload),
            timeout=10,
        )
        if response.status_code == 201:
            print(f"[BREVO SMS] ✅ SMS enviado correctamente a {telefono_limpio}")
        else:
            print(f"[BREVO SMS] ❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[BREVO SMS] ❌ Excepción al enviar SMS: {e}")


def enviar_correo_confirmacion(nombre, email, empresa, telefono, descripcion):
    """Envía un correo de confirmación al lead usando la API transaccional de Brevo."""
    if not BREVO_API_KEY:
        print("Brevo: BREVO_API_KEY no configurada, se omite el envío de correo.")
        return

    lead_id = format(abs(hash(nombre + email)) % 0xFFFFFF, '06X')
    tel_border = "border-bottom:1px solid rgba(0,212,255,.06);" if empresa or descripcion else ""

    empresa_row = f"""
        <tr>
          <td style="padding:9px 14px;border-bottom:1px solid rgba(0,212,255,.06);font-size:8.5px;color:rgba(0,212,255,.42);letter-spacing:2px;width:32%;">EMPRESA</td>
          <td style="padding:9px 14px;border-bottom:1px solid rgba(0,212,255,.06);font-size:12px;color:#ddd;">{empresa}</td>
        </tr>""" if empresa else ""

    descripcion_row = f"""
        <tr>
          <td style="padding:9px 14px;font-size:8.5px;color:rgba(0,212,255,.42);letter-spacing:2px;width:32%;">PROYECTO</td>
          <td style="padding:9px 14px;font-size:12px;color:#ddd;">{descripcion}</td>
        </tr>""" if descripcion else ""

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Solicitud Recibida — AUT</title>
  <style>
    @keyframes neonPulse {{
      0%,100% {{ border-color:rgba(0,212,255,.22); }}
      50%      {{ border-color:rgba(0,212,255,.7); box-shadow:0 0 30px rgba(0,212,255,.1); }}
    }}
    @keyframes ringPing {{
      0%,100% {{ box-shadow:0 0 0 0 rgba(0,212,255,.55); }}
      50%      {{ box-shadow:0 0 0 16px rgba(0,212,255,0); }}
    }}
    @keyframes checkPop {{
      0%   {{ transform:scale(0) rotate(-30deg); opacity:0; }}
      60%  {{ transform:scale(1.35) rotate(6deg); opacity:1; }}
      100% {{ transform:scale(1) rotate(0deg); opacity:1; }}
    }}
    @keyframes glow {{
      0%,100% {{ text-shadow:0 0 8px rgba(0,212,255,.3); }}
      50%      {{ text-shadow:0 0 22px rgba(0,212,255,.9),0 0 45px rgba(0,212,255,.25); }}
    }}
    @keyframes slideUp {{
      from {{ opacity:0; transform:translateY(12px); }}
      to   {{ opacity:1; transform:translateY(0); }}
    }}
    @keyframes barFill {{
      from {{ width:0%; }}
      to   {{ width:100%; }}
    }}
    @keyframes blink {{ 50% {{ opacity:0; }} }}
    @keyframes fadeIn {{
      from {{ opacity:0; }}
      to   {{ opacity:1; }}
    }}
    .wrap  {{ animation:fadeIn .8s ease both; }}
    .card  {{ animation:neonPulse 3.5s ease-in-out infinite; }}
    .ring  {{ animation:ringPing 2.5s ease-in-out infinite; }}
    .check {{ animation:checkPop .65s .3s cubic-bezier(.34,1.6,.64,1) both; }}
    .title {{ animation:glow 3s ease-in-out infinite; }}
    .r1    {{ animation:slideUp .5s .2s ease both; }}
    .r2    {{ animation:slideUp .5s .35s ease both; }}
    .r3    {{ animation:slideUp .5s .5s ease both; }}
    .r4    {{ animation:slideUp .5s .65s ease both; }}
    .r5    {{ animation:slideUp .5s .8s ease both; }}
    .r6    {{ animation:slideUp .5s .95s ease both; }}
    .bar   {{ animation:barFill 1.5s .5s cubic-bezier(.16,1,.3,1) both; }}
    .cur   {{ animation:blink 1s step-end infinite; }}
    .log1  {{ animation:slideUp .45s .8s ease both; }}
    .log2  {{ animation:slideUp .45s 1.0s ease both; }}
    .log3  {{ animation:slideUp .45s 1.2s ease both; }}
  </style>
</head>
<body style="margin:0;padding:0;background:#050505;font-family:'Courier New',monospace;">
<div class="wrap">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#050505;padding:36px 16px;">
<tr><td align="center">
<table class="card" width="560" cellpadding="0" cellspacing="0"
       style="background:#0a0a0a;border:1px solid rgba(0,212,255,.22);max-width:560px;width:100%;">

  <!-- HEADER -->
  <tr>
    <td style="padding:28px 34px 22px;
               background:linear-gradient(135deg,rgba(0,212,255,.04) 0%,transparent 65%);
               border-bottom:1px solid rgba(0,212,255,.1);">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="vertical-align:middle;">
            <p style="margin:0 0 5px;font-size:9px;color:rgba(0,212,255,.48);letter-spacing:5px;">
              // SISTEMA AUT &nbsp;<span class="cur" style="color:rgba(0,212,255,.48);">&#9608;</span>
            </p>
            <h1 class="title"
                style="margin:0 0 6px;font-size:21px;font-weight:700;color:#00d4ff;
                       letter-spacing:6px;text-transform:uppercase;
                       text-shadow:0 0 8px rgba(0,212,255,.3);">
              SOLICITUD RECIBIDA
            </h1>
            <p style="margin:0;font-size:9px;color:rgba(0,212,255,.28);letter-spacing:2px;">
              ID:&nbsp;<span style="color:rgba(0,212,255,.52);">{lead_id}</span>
              &nbsp;·&nbsp;
              STATUS:&nbsp;<span style="color:rgba(0,255,140,.65);">&#9679; PROCESADO</span>
            </p>
          </td>
          <td align="right" style="vertical-align:middle;padding-left:16px;">
            <div class="ring"
                 style="width:56px;height:56px;border-radius:50%;
                        border:2px solid rgba(0,212,255,.65);">
              <table width="56" height="56" cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center" style="vertical-align:middle;">
                    <span class="check"
                          style="font-size:22px;color:#00d4ff;display:inline-block;
                                 text-shadow:0 0 14px rgba(0,212,255,.85);">&#10003;</span>
                  </td>
                </tr>
              </table>
            </div>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- GREETING -->
  <tr class="r1">
    <td style="padding:24px 34px 0;">
      <p style="margin:0;font-size:13.5px;color:#bbb;line-height:1.85;">
        Hola&nbsp;<strong style="color:#e6e6e6;">{nombre}</strong>,<br>
        tu solicitud fue recibida y procesada correctamente.<br>
        En las pr&oacute;ximas&nbsp;<strong style="color:#00d4ff;">12 horas</strong>&nbsp;nuestra
        asesora te contactar&aacute; personalmente.
      </p>
    </td>
  </tr>

  <!-- PIPELINE STATUS BAR -->
  <tr class="r2">
    <td style="padding:20px 34px 0;">
      <p style="margin:0 0 8px;font-size:8.5px;color:rgba(0,212,255,.38);letter-spacing:4px;">
        PIPELINE STATUS
      </p>
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="background:rgba(0,212,255,.06);height:4px;border-radius:2px;overflow:hidden;">
            <div class="bar"
                 style="height:4px;width:100%;border-radius:2px;
                        background:linear-gradient(90deg,#00d4ff,rgba(0,212,255,.5));
                        box-shadow:0 0 10px rgba(0,212,255,.6);">
            </div>
          </td>
        </tr>
      </table>
      <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:7px;">
        <tr>
          <td style="font-size:8px;color:rgba(0,212,255,.28);letter-spacing:1px;">&#9658; RECIBIDO</td>
          <td align="center" style="font-size:8px;color:rgba(0,212,255,.28);letter-spacing:1px;">&#9658; VALIDADO</td>
          <td align="right" style="font-size:8px;color:rgba(0,212,255,.55);letter-spacing:1px;">&#9658; ASIGNADO &#9679;</td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- DATA TABLE -->
  <tr class="r3">
    <td style="padding:20px 34px 0;">
      <p style="margin:0 0 9px;font-size:8.5px;color:rgba(0,212,255,.38);letter-spacing:4px;">
        RESUMEN DE SOLICITUD
      </p>
      <table width="100%" cellpadding="0" cellspacing="0"
             style="border:1px solid rgba(0,212,255,.1);background:rgba(0,212,255,.015);">
        <tr>
          <td style="padding:9px 14px;border-bottom:1px solid rgba(0,212,255,.06);
                     font-size:8.5px;color:rgba(0,212,255,.42);letter-spacing:2px;width:32%;">
            NOMBRE
          </td>
          <td style="padding:9px 14px;border-bottom:1px solid rgba(0,212,255,.06);
                     font-size:12px;color:#ddd;">
            {nombre}
          </td>
        </tr>
        <tr>
          <td style="padding:9px 14px;border-bottom:1px solid rgba(0,212,255,.06);
                     font-size:8.5px;color:rgba(0,212,255,.42);letter-spacing:2px;">
            EMAIL
          </td>
          <td style="padding:9px 14px;border-bottom:1px solid rgba(0,212,255,.06);
                     font-size:12px;color:#ddd;">
            {email}
          </td>
        </tr>
        <tr>
          <td style="padding:9px 14px;{tel_border}font-size:8.5px;color:rgba(0,212,255,.42);letter-spacing:2px;">
            TEL&Eacute;FONO
          </td>
          <td style="padding:9px 14px;{tel_border}font-size:12px;color:#ddd;">
            {telefono}
          </td>
        </tr>
        {empresa_row}
        {descripcion_row}
      </table>
    </td>
  </tr>

  <!-- TERMINAL LOG -->
  <tr class="r4">
    <td style="padding:18px 34px 0;">
      <table width="100%" cellpadding="0" cellspacing="0"
             style="background:rgba(0,0,0,.45);border:1px solid rgba(0,212,255,.08);
                    padding:13px 15px;">
        <tr class="log1">
          <td style="padding-bottom:5px;font-size:10px;font-family:'Courier New',monospace;
                     letter-spacing:.5px;color:#333;">
            &gt;&nbsp;<span style="color:rgba(0,212,255,.65);">[OK]</span>&nbsp;
            <span style="color:#3a3a3a;">Datos recibidos y validados</span>
          </td>
        </tr>
        <tr class="log2">
          <td style="padding-bottom:5px;font-size:10px;font-family:'Courier New',monospace;
                     letter-spacing:.5px;color:#333;">
            &gt;&nbsp;<span style="color:rgba(0,212,255,.65);">[OK]</span>&nbsp;
            <span style="color:#3a3a3a;">Notificaci&oacute;n enviada al equipo</span>
          </td>
        </tr>
        <tr class="log3">
          <td style="font-size:10px;font-family:'Courier New',monospace;
                     letter-spacing:.5px;color:#333;">
            &gt;&nbsp;<span style="color:rgba(0,212,255,.65);">[OK]</span>&nbsp;
            <span style="color:#3a3a3a;">Pipeline de contacto iniciado</span>&nbsp;
            <span class="cur" style="color:rgba(0,212,255,.4);">&#9608;</span>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- CONTACT PILLS -->
  <tr class="r5">
    <td style="padding:18px 34px 0;" align="center">
      <table cellpadding="0" cellspacing="0">
        <tr>
          <td style="padding:8px 16px;border:1px solid rgba(0,212,255,.2);
                     font-size:9px;color:rgba(0,212,255,.6);
                     letter-spacing:2px;white-space:nowrap;">
            &#128172;&nbsp;&nbsp;V&Iacute;A WHATSAPP
          </td>
          <td width="10"></td>
          <td style="padding:8px 16px;border:1px solid rgba(0,212,255,.2);
                     font-size:9px;color:rgba(0,212,255,.6);
                     letter-spacing:2px;white-space:nowrap;">
            &#128231;&nbsp;&nbsp;V&Iacute;A EMAIL
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- SECURITY BADGE -->
  <tr class="r6">
    <td style="padding:18px 34px 0;">
      <table width="100%" cellpadding="0" cellspacing="0"
             style="border:1px solid rgba(0,212,255,.07);
                    background:rgba(0,212,255,.015);padding:12px 14px;">
        <tr>
          <td width="26" style="vertical-align:top;padding-top:1px;font-size:17px;">&#128274;</td>
          <td style="padding-left:10px;font-size:9px;color:rgba(0,212,255,.3);
                     line-height:1.7;letter-spacing:.5px;">
            <strong style="color:rgba(0,212,255,.52);letter-spacing:2px;
                           display:block;margin-bottom:2px;font-size:8.5px;">
              CIFRADO AES-256 &middot; EXTREMO A EXTREMO
            </strong>
            Tus datos est&aacute;n protegidos. Zero-logs &middot; Transmisi&oacute;n segura &middot; Sin acceso de terceros.
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- FOOTER -->
  <tr>
    <td style="padding:20px 34px 22px;border-top:1px solid rgba(0,212,255,.07);">
      <p style="margin:0;font-size:8.5px;color:#252525;letter-spacing:3px;text-align:center;">
        SISTEMA AUT &mdash; AUTOMATIZACI&Oacute;N INTELIGENTE &nbsp;&middot;&nbsp; &copy; 2026
      </p>
      <p style="margin:6px 0 0;font-size:8px;color:#1c1c1c;text-align:center;letter-spacing:1px;">
        Si no realizaste esta solicitud, puedes ignorar este mensaje.
      </p>
    </td>
  </tr>

</table>
</td></tr>
</table>
</div>
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
        if response.status_code == 201:
            print(f"[BREVO] ✅ Correo enviado correctamente a {email}")
        else:
            print(f"[BREVO] ❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[BREVO] ❌ Excepción al enviar correo: {e}")


@app.route('/health')
def health():
    """Endpoint de diagnóstico — muestra qué variables están configuradas."""
    from flask import jsonify
    return jsonify({
        "TELEGRAM_TOKEN":   "OK" if TOKEN        else "NO CONFIGURADO",
        "TELEGRAM_CHAT_ID": "OK" if CHAT_ID      else "NO CONFIGURADO",
        "BREVO_API_KEY":    "OK" if BREVO_API_KEY else "NO CONFIGURADO",
        "SENDER_EMAIL":     SENDER_EMAIL,
        "SENDER_NAME":      SENDER_NAME,
    })


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

        # Enviamos SMS de confirmación al número registrado
        enviar_sms_confirmacion(nombre, telefono)

        return render_template('registro.html')
    return render_template('index.html')

if __name__ == '__main__':
    # Render asigna el puerto automáticamente, si no, usamos el 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
