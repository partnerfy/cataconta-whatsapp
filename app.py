# app.py
import os
from flask import Flask, request, Response

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "CataConta WhatsApp Webhook ativo!"

@app.route("/whatsapp/webhook", methods=["POST"])
def whatsapp_webhook():
    # Twilio envia application/x-www-form-urlencoded
    from_number = request.form.get("From")           # ex: 'whatsapp:+55...'
    to_number   = request.form.get("To")             # ex: 'whatsapp:+1415...'
    body        = request.form.get("Body")           # texto da mensagem
    num_media   = int(request.form.get("NumMedia", "0"))
    media_url0  = request.form.get("MediaUrl0") if num_media > 0 else None

    print("---- INBOUND WHATSAPP ----")
    print(f"From: {from_number}")
    print(f"To:   {to_number}")
    print(f"Body: {body}")
    print(f"NumMedia: {num_media}  MediaUrl0: {media_url0}")
    print("---------------------------")

    # Monte a mensagem de confirmação (simples)
    if body:
        reply_text = f"✅ Recebi: {body[:120]}"
    elif media_url0:
        reply_text = "📎 Recebi sua mídia! (vou processar e te aviso)."
    else:
        reply_text = "✅ Recebi sua mensagem!"

    # TwiML para responder via WhatsApp
    twiml = f"<Response><Message>{reply_text}</Message></Response>"
    return Response(twiml, mimetype="text/xml")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render usa PORT
    app.run(host="0.0.0.0", port=port)

