# app.py
import os
from flask import Flask, request, jsonify, Response

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify(ok=True)

@app.route("/", methods=["GET"])
def home():
    return "CataConta WhatsApp Webhook ativo!"

@app.route("/whatsapp/webhook", methods=["POST", "GET"])
def whatsapp_webhook():
    # Algumas checagens (ou o próprio Twilio) podem fazer GET: responda OK
    if request.method == "GET":
        return Response(
            '<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            mimetype="application/xml",
            status=200
        )

    # Twilio envia application/x-www-form-urlencoded
    from_number = request.form.get("From", "")          # ex.: 'whatsapp:+55...'
    body        = (request.form.get("Body") or "").strip()
    num_media   = int(request.form.get("NumMedia", "0"))
    media_url0  = request.form.get("MediaUrl0") if num_media > 0 else None

    # Logs de diagnóstico
    print("---- INBOUND ----")
    print(f"From: {from_number}")
    print(f"Body: {body}")
    print(f"NumMedia: {num_media} | MediaUrl0: {media_url0}")
    print("------------------")

    # Mensagem de retorno (curta e direta)
    if body:
        reply_text = f"✅ Recebi: {body[:120]}"
    elif media_url0:
        reply_text = "📎 Recebi sua mídia! (vou processar)."
    else:
        reply_text = "✅ Recebi sua mensagem!"

    # Responde via TwiML: o Twilio envia essa mensagem imediatamente ao remetente
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Message>{reply_text}</Message>
</Response>'''
    return Response(xml, mimetype="application/xml", status=200)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
