import os
from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# Tus credenciales integradas
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def notificar_telegram(nombre, email):
    mensaje = f"🚀 ¡Nuevo lead de automatización!\n👤 Nombre: {nombre}\n📧 Email: {email}"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje}
    
    try:
        response = requests.post(url, data=payload)
        # Esto imprimirá en la consola lo que Telegram responde (sea bueno o malo)
        print("Respuesta de Telegram:", response.text) 
    except Exception as e:
        print(f"Error grave al conectar: {e}")

@app.route('/')
def inicio():
    return render_template('index.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        
        # Disparamos la notificación a Telegram
        notificar_telegram(nombre, email)
        
        return f"¡Registro exitoso para {nombre}! Revisa tu Telegram celular 😎"
        
    return render_template('registro.html')

if __name__ == '__main__':
    # Usamos 0.0.0.0 para que Docker pueda exponer el puerto correctamente
    app.run(host='0.0.0.0', port=5000)
