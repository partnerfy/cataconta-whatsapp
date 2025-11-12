# app.py
import os, threading
from flask import Flask, request, jsonify
from twilio.rest import Client

app = Flask(__name__)

# Variáveis de ambiente (colocaremos no Render no passo 3)
TWILIO_SID   = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM  = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")  # número do Sandbox

client = Client(TWILIO_SID, TWILIO_TOKEN) if (TWILIO_SID and TWILIO_TOKEN) else None

@app.route("/health", methods=["GET"])
def health():
    return jsonify(ok=True)

@app.route("/", methods=["GET"])
def home():
    return "CataConta WhatsApp Webhook ativo!"

def _send_whatsapp(to_number: str, text: str):
    # Envia resposta via API da Twilio (em background)
    if not client or not (to_number and to_number.startswith("whatsapp:")):
        print("[TWILIO SKIP] client ausente ou 'to' inválido:", to_number)
        return
    try:
        msg = client.messages.create(from_=TWILIO_FROM, to=to_number, body=text)
        print(f"[TWILIO OK] sid={msg.sid}")
    except Exception as e:
        print(f"[TWILIO ERROR] {e}")

@app.route("/whatsapp/webhook", methods=["POST"])
def whatsapp_webhook():
    # Twilio envia application/x-www-form-urlencoded
    from_number = request.form.get("From", "")       # ex.: 'whatsapp:+55...'
    body        = request.form.get("Body", "")       # texto
    num_media   = int(request.form.get("NumMedia", "0"))
    media_url0  = request.form.get("MediaUrl0") if num_media > 0 else None

    print("---- INBOUND ----")
    print(f"From: {from_number}")
    print(f"Body: {body}")
    print(f"NumMedia: {num_media} | MediaUrl0: {media_url0}")
    print("------------------")

    # Mensagem de retorno
    if body:
        reply_text = f"✅ Recebi: {body[:120]}"
    elif media_url0:
        reply_text = "📎 Recebi sua mídia! (vou processar)."
    else:
        reply_text = "✅ Recebi sua mensagem!"

    # Envia resposta sem bloquear o retorno ao Twilio
    if from_number:
        threading.Thread(target=_send_whatsapp, args=(from_number, reply_text), daemon=True).start()

    # ACK rápido (202) evita timeouts/502 no Twilio
    return jsonify(status="accepted"), 202

# Não use app.run com gunicorn no Render
