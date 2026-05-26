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
        "unicodeEnabled": False,
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
        print(f"[BREVO SMS] Status: {response.status_code} | Body: {response.text}")
        if response.status_code == 201:
            print(f"[BREVO SMS] ✅ SMS enviado a {telefono_limpio}")
        else:
            print(f"[BREVO SMS] ❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[BREVO SMS] ❌ Excepción: {e}")


def enviar_correo_confirmacion(nombre, email, empresa, telefono, descripcion):
    """Envía un correo de confirmación al lead usando la API transaccional de Brevo."""
    if not BREVO_API_KEY:
        print("Brevo: BREVO_API_KEY no configurada, se omite el envío de correo.")
        return

    lead_id = format(abs(hash(nombre + email)) % 0xFFFFFF, '06X')
    tel_border = "border-bottom:1px solid rgba(0,212,255,.06);" if empresa or descripcion else ""

    empresa_row = f"""
          <tr>
            <td style="padding:10px 16px;width:30%;border-bottom:1px solid rgba(0,212,255,.07);font-size:8px;color:rgba(0,212,255,.45);letter-spacing:3px;">EMPRESA</td>
            <td style="padding:10px 16px;border-bottom:1px solid rgba(0,212,255,.07);font-size:12px;color:#ddd;">{empresa}</td>
          </tr>""" if empresa else ""

    descripcion_row = f"""
          <tr>
            <td style="padding:10px 16px;width:30%;font-size:8px;color:rgba(0,212,255,.45);letter-spacing:3px;">PROYECTO</td>
            <td style="padding:10px 16px;font-size:12px;color:#ddd;">{descripcion}</td>
          </tr>""" if descripcion else ""

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Solicitud Recibida — SISTEMA AUT</title>
  <style>
    @keyframes neonPulse {{
      0%,100% {{ border-color:rgba(0,212,255,.28); box-shadow:0 0 20px rgba(0,212,255,.04); }}
      50%      {{ border-color:rgba(0,212,255,.85); box-shadow:0 0 45px rgba(0,212,255,.13); }}
    }}
    @keyframes glow {{
      0%,100% {{ text-shadow:0 0 10px rgba(0,212,255,.4); }}
      50%      {{ text-shadow:0 0 28px rgba(0,212,255,1),0 0 55px rgba(0,212,255,.3); }}
    }}
    @keyframes checkPop {{
      0%   {{ transform:scale(0) rotate(-20deg); opacity:0; }}
      65%  {{ transform:scale(1.32) rotate(5deg); opacity:1; }}
      100% {{ transform:scale(1) rotate(0deg); opacity:1; }}
    }}
    @keyframes ringPing {{
      0%,100% {{ box-shadow:0 0 0 0 rgba(0,212,255,.5); }}
      50%      {{ box-shadow:0 0 0 14px rgba(0,212,255,0); }}
    }}
    @keyframes barFill {{
      from {{ width:0%; }}
      to   {{ width:100%; }}
    }}
    @keyframes blink {{ 50% {{ opacity:0; }} }}
    @keyframes slideUp {{
      from {{ opacity:0; transform:translateY(14px); }}
      to   {{ opacity:1; transform:translateY(0); }}
    }}
    @keyframes fadeIn {{
      from {{ opacity:0; }}
      to   {{ opacity:1; }}
    }}
    .wrap  {{ animation:fadeIn .7s ease both; }}
    .outer {{ animation:neonPulse 3.5s ease-in-out infinite; }}
    .title {{ animation:glow 3s ease-in-out infinite; }}
    .ring  {{ animation:ringPing 2.5s ease-in-out infinite; }}
    .chk   {{ animation:checkPop .65s .35s cubic-bezier(.34,1.6,.64,1) both; }}
    .bar   {{ animation:barFill 1.5s .5s cubic-bezier(.16,1,.3,1) both; }}
    .cur   {{ animation:blink 1s step-end infinite; }}
    .r1    {{ animation:slideUp .5s .15s ease both; }}
    .r2    {{ animation:slideUp .5s .30s ease both; }}
    .r3    {{ animation:slideUp .5s .45s ease both; }}
    .r4    {{ animation:slideUp .5s .60s ease both; }}
    .r5    {{ animation:slideUp .5s .75s ease both; }}
    .r6    {{ animation:slideUp .5s .90s ease both; }}
    .r7    {{ animation:slideUp .5s 1.05s ease both; }}
  </style>
</head>
<body style="margin:0;padding:0;background:#030303;font-family:'Courier New',Courier,monospace;">
<div class="wrap">
<table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#030303"
       style="background:#030303;padding:40px 16px;">
<tr><td align="center" bgcolor="#030303">

<!-- ═══ CARD ═══ -->
<table class="outer" width="580" cellpadding="0" cellspacing="0" border="0" bgcolor="#070707"
       style="max-width:580px;width:100%;background:#070707;
              border:1px solid rgba(0,212,255,.3);
              box-shadow:0 0 70px rgba(0,212,255,.06);">

  <!-- TOP SCAN LINE -->
  <tr>
    <td height="2" style="height:2px;font-size:0;line-height:0;
        background:linear-gradient(90deg,transparent 5%,#00d4ff 50%,transparent 95%);">&nbsp;</td>
  </tr>

  <!-- HEADER -->
  <tr>
    <td style="padding:30px 36px 24px;
               background:linear-gradient(135deg,rgba(0,212,255,.06) 0%,transparent 55%);
               border-bottom:1px solid rgba(0,212,255,.08);">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="vertical-align:middle;">
            <p style="margin:0 0 7px;font-size:8px;color:rgba(0,212,255,.42);letter-spacing:5px;">
              // SISTEMA AUT &nbsp;<span class="cur" style="color:rgba(0,212,255,.4);">&#9608;</span>
            </p>
            <h1 class="title"
                style="margin:0 0 8px;font-size:22px;font-weight:700;color:#00d4ff;
                       letter-spacing:7px;text-transform:uppercase;
                       text-shadow:0 0 12px rgba(0,212,255,.5);">
              SOLICITUD RECIBIDA
            </h1>
            <p style="margin:0;font-size:8px;color:rgba(0,212,255,.28);letter-spacing:2px;">
              REF:&nbsp;<span style="color:rgba(0,212,255,.6);">{lead_id}</span>
              &nbsp;&nbsp;&#183;&nbsp;&nbsp;
              <span style="color:rgba(0,255,150,.75);">&#9679;&nbsp;PROCESADO</span>
            </p>
          </td>
          <td align="right" style="vertical-align:middle;padding-left:20px;white-space:nowrap;">
            <div class="ring"
                 style="display:inline-block;width:58px;height:58px;border-radius:50%;
                        border:2px solid rgba(0,212,255,.65);
                        background:rgba(0,212,255,.05);">
              <table width="58" height="58" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td align="center" style="vertical-align:middle;">
                    <span class="chk"
                          style="font-size:25px;color:#00d4ff;display:inline-block;font-weight:700;
                                 text-shadow:0 0 18px rgba(0,212,255,.9);">&#10003;</span>
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
    <td style="padding:26px 36px 0;">
      <p style="margin:0;font-size:14px;color:#aaaaaa;line-height:2;
                font-family:'Courier New',Courier,monospace;">
        Hola&nbsp;<strong style="color:#ffffff;">{nombre}</strong>,<br>
        tu solicitud fue <strong style="color:#00d4ff;">recibida y procesada</strong> correctamente.<br>Un asesor te contactar&aacute; en las pr&oacute;ximas
        <strong style="color:#00d4ff;">12&nbsp;horas</strong>.
      </p>
    </td>
  </tr>

  <!-- PIPELINE STATUS -->
  <tr class="r2">
    <td style="padding:22px 36px 0;">
      <p style="margin:0 0 9px;font-size:8px;color:rgba(0,212,255,.38);letter-spacing:5px;">
        PIPELINE STATUS
      </p>
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="background:rgba(0,212,255,.07);height:4px;border-radius:2px;overflow:hidden;">
            <div class="bar"
                 style="height:4px;width:100%;border-radius:2px;
                        background:linear-gradient(90deg,#00d4ff,rgba(0,212,255,.45));
                        box-shadow:0 0 12px rgba(0,212,255,.65);">&nbsp;</div>
          </td>
        </tr>
      </table>
      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:8px;">
        <tr>
          <td style="font-size:7.5px;color:rgba(0,212,255,.35);letter-spacing:1px;">&#9658;&nbsp;RECIBIDO</td>
          <td align="center" style="font-size:7.5px;color:rgba(0,212,255,.35);letter-spacing:1px;">&#9658;&nbsp;VALIDADO</td>
          <td align="right" style="font-size:7.5px;color:rgba(0,212,255,.7);letter-spacing:1px;">&#9658;&nbsp;ASIGNADO&nbsp;&#9679;</td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- DATA TABLE -->
  <tr class="r3">
    <td style="padding:22px 36px 0;">
      <p style="margin:0 0 10px;font-size:8px;color:rgba(0,212,255,.38);letter-spacing:5px;">
        RESUMEN DE SOLICITUD
      </p>
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="border:1px solid rgba(0,212,255,.12);background:rgba(0,212,255,.016);">
        <tr>
          <td style="padding:10px 16px;width:30%;border-bottom:1px solid rgba(0,212,255,.07);
                     font-size:8px;color:rgba(0,212,255,.45);letter-spacing:3px;">NOMBRE</td>
          <td style="padding:10px 16px;border-bottom:1px solid rgba(0,212,255,.07);
                     font-size:12px;color:#ddd;">{nombre}</td>
        </tr>
        <tr>
          <td style="padding:10px 16px;width:30%;border-bottom:1px solid rgba(0,212,255,.07);
                     font-size:8px;color:rgba(0,212,255,.45);letter-spacing:3px;">EMAIL</td>
          <td style="padding:10px 16px;border-bottom:1px solid rgba(0,212,255,.07);
                     font-size:12px;color:#ddd;">{email}</td>
        </tr>
        <tr>
          <td style="padding:10px 16px;width:30%;{tel_border}font-size:8px;color:rgba(0,212,255,.45);letter-spacing:3px;">TEL&Eacute;FONO</td>
          <td style="padding:10px 16px;{tel_border}font-size:12px;color:#ddd;">{telefono}</td>
        </tr>
        {empresa_row}
        {descripcion_row}
      </table>
    </td>
  </tr>

  <!-- TERMINAL LOG -->
  <tr class="r4">
    <td style="padding:22px 36px 0;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="background:rgba(0,0,0,.6);border:1px solid rgba(0,212,255,.08);">
        <tr>
          <td style="padding:14px 16px;">
            <div style="font-size:10px;margin-bottom:6px;font-family:'Courier New',Courier,monospace;">
              &gt;&nbsp;<span style="color:rgba(0,212,255,.7);">[&nbsp;OK&nbsp;]</span>&nbsp;
              <span style="color:#666666;">Lead registrado &mdash; REF:{lead_id}</span>
            </div>
            <div style="font-size:10px;margin-bottom:6px;font-family:'Courier New',Courier,monospace;">
              &gt;&nbsp;<span style="color:rgba(0,212,255,.7);">[&nbsp;OK&nbsp;]</span>&nbsp;
              <span style="color:#666666;">Notificaci&oacute;n enviada al equipo AUT</span>
            </div>
            <div style="font-size:10px;font-family:'Courier New',Courier,monospace;">
              &gt;&nbsp;<span style="color:rgba(0,212,255,.7);">[&nbsp;OK&nbsp;]</span>&nbsp;
              <span style="color:#666666;">Pipeline de contacto activo</span>&nbsp;
              <span class="cur" style="color:rgba(0,212,255,.45);">&#9608;</span>
            </div>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- WHAT HAPPENS NEXT -->
  <tr class="r5">
    <td style="padding:22px 36px 0;">
      <p style="margin:0 0 12px;font-size:8px;color:rgba(0,212,255,.38);letter-spacing:5px;">
        // QU&Eacute; PASA AHORA
      </p>
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="width:48%;vertical-align:top;padding:12px 14px;
                     border:1px solid rgba(0,212,255,.1);background:rgba(0,212,255,.018);">
            <div style="font-size:7.5px;color:rgba(0,212,255,.5);letter-spacing:2px;margin-bottom:5px;">PASO&nbsp;01</div>
            <div style="font-size:11px;color:#ccc;line-height:1.75;">Asesor&iacute;a gratuita en<br>menos de <strong style="color:#00d4ff;">12&nbsp;horas</strong></div>
          </td>
          <td style="width:4%;">&nbsp;</td>
          <td style="width:48%;vertical-align:top;padding:12px 14px;
                     border:1px solid rgba(0,212,255,.1);background:rgba(0,212,255,.018);">
            <div style="font-size:7.5px;color:rgba(0,212,255,.5);letter-spacing:2px;margin-bottom:5px;">PASO&nbsp;02</div>
            <div style="font-size:11px;color:#ccc;line-height:1.75;">Propuesta a medida<br>seg&uacute;n tu presupuesto</div>
          </td>
        </tr>
        <tr><td colspan="3" style="height:6px;"></td></tr>
        <tr>
          <td style="width:48%;vertical-align:top;padding:12px 14px;
                     border:1px solid rgba(0,212,255,.1);background:rgba(0,212,255,.018);">
            <div style="font-size:7.5px;color:rgba(0,212,255,.5);letter-spacing:2px;margin-bottom:5px;">PASO&nbsp;03</div>
            <div style="font-size:11px;color:#ccc;line-height:1.75;">Desarrollo con entregas<br>parciales y visibles</div>
          </td>
          <td style="width:4%;">&nbsp;</td>
          <td style="width:48%;vertical-align:top;padding:12px 14px;
                     border:1px solid rgba(0,212,255,.1);background:rgba(0,212,255,.018);">
            <div style="font-size:7.5px;color:rgba(0,212,255,.5);letter-spacing:2px;margin-bottom:5px;">PASO&nbsp;04</div>
            <div style="font-size:11px;color:#ccc;line-height:1.75;">Entrega + capacitaci&oacute;n<br>+ soporte incluido</div>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- CONTACT CHANNELS -->
  <tr class="r6">
    <td style="padding:22px 36px 0;" align="center">
      <p style="margin:0 0 12px;font-size:8px;color:rgba(0,212,255,.28);letter-spacing:3px;">
        TE CONTACTAREMOS V&Iacute;A
      </p>
      <table cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="padding:9px 16px;border:1px solid rgba(0,212,255,.22);
                     font-size:8.5px;color:rgba(0,212,255,.65);letter-spacing:2px;white-space:nowrap;">
            &#128172;&nbsp;&nbsp;WHATSAPP
          </td>
          <td width="10">&nbsp;</td>
          <td style="padding:9px 16px;border:1px solid rgba(0,212,255,.22);
                     font-size:8.5px;color:rgba(0,212,255,.65);letter-spacing:2px;white-space:nowrap;">
            &#128231;&nbsp;&nbsp;EMAIL
          </td>
          <td width="10">&nbsp;</td>
          <td style="padding:9px 16px;border:1px solid rgba(0,212,255,.22);
                     font-size:8.5px;color:rgba(0,212,255,.65);letter-spacing:2px;white-space:nowrap;">
            &#128241;&nbsp;&nbsp;LLAMADA
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- SECURITY BADGE -->
  <tr class="r7">
    <td style="padding:22px 36px 0;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="border:1px solid rgba(0,212,255,.08);background:rgba(0,212,255,.014);">
        <tr>
          <td width="34" style="padding:12px 0 12px 14px;vertical-align:middle;font-size:18px;">&#128274;</td>
          <td style="padding:12px 14px 12px 8px;font-size:9px;color:rgba(0,212,255,.3);line-height:1.8;">
            <strong style="color:rgba(0,212,255,.52);letter-spacing:2px;font-size:8px;display:block;margin-bottom:3px;">
              CIFRADO AES-256 &middot; EXTREMO A EXTREMO
            </strong>
            Tus datos est&aacute;n protegidos &middot; Zero-logs &middot;
            Transmisi&oacute;n segura &middot; Sin acceso de terceros
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- FOOTER -->
  <tr>
    <td style="padding:22px 36px 26px;border-top:1px solid rgba(0,212,255,.07);">
      <p style="margin:0 0 5px;font-size:8.5px;color:#444444;letter-spacing:3px;text-align:center;">
        SISTEMA AUT &mdash; AUTOMATIZACI&Oacute;N INTELIGENTE &nbsp;&middot;&nbsp; &copy; 2026
      </p>
      <p style="margin:0;font-size:8px;color:#555555;text-align:center;letter-spacing:1px;">
        Si no realizaste esta solicitud puedes ignorar este mensaje.
      </p>
    </td>
  </tr>

  <!-- BOTTOM SCAN LINE -->
  <tr>
    <td height="2" style="height:2px;font-size:0;line-height:0;
        background:linear-gradient(90deg,transparent 5%,rgba(0,212,255,.45) 50%,transparent 95%);">&nbsp;</td>
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
