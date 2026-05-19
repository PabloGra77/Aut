import os
from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# Configuración usando variables de entorno (Las que pusiste en Render)
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

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
        
        # Disparamos la notificación
        notificar_telegram(nombre, email, empresa, telefono, descripcion)
        
        return render_template('registro.html')
    return render_template('index.html')

if __name__ == '__main__':
    # Render asigna el puerto automáticamente, si no, usamos el 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
