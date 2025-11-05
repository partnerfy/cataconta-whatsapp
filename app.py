# app.py
import os
from flask import Flask, request, Response

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "CataConta WhatsApp Webhook ativo!"

@app.route("/whatsapp/webhook", methods=["POST"])
def whatsapp_webhook():
    from_number = request.form.get("From")           # ex.: 'whatsapp:+55...'
    body        = request.form.get("Body") or ""
    num_media   = int(request.form.get("NumMedia", "0"))
    media_url0  = request.form.get("MediaUrl0") if num_media > 0 else None

    print("---- INBOUND ----")
    print(f"From: {from_number}")
    print(f"Body: {body}")
    print(f"NumMedia: {num_media} MediaUrl0: {media_url0}")
    print("-------------------")

    if body:
        reply_text = f"✅ Recebi: {body[:120]}"
    elif media_url0:
        reply_text = "📎 Recebi sua mídia! (vou processar)."
    else:
        reply_text = "✅ Recebi sua mensagem!"

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Message>{reply_text}</Message>
</Response>"""
    return Response(xml, headers={"Content-Type": "application/xml"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render define PORT
    app.run(host="0.0.0.0", port=port)

