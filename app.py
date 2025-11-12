# app.py
import os
import re
from flask import Flask, request, jsonify, Response
# twilio.rest não é mais necessário se você optar só por TwiML
# from twilio.rest import Client

app = Flask(__name__)

# (Opcional) Se quiser manter health/diagnóstico
@app.route("/health", methods=["GET"])
def health():
    return jsonify(ok=True)

@app.route("/", methods=["GET"])
def home():
    return "CataConta WhatsApp Webhook ativo!"

# --- util: normalização BR (mantive para referência futura, se usar API) ---
def normalize_whatsapp_br(to_number: str) -> str:
    m = re.fullmatch(r'whatsapp:\+55(\d{2})(\d{8})', to_number)
    if m:
        ddd, base = m.groups()
        fixed = f"whatsapp:+55{ddd}9{base}"
        print(f"[NORMALIZE] Corrigido número BR: {to_number} -> {fixed}")
        return fixed
    return to_number

@app.route("/whatsapp/webhook", methods=["POST", "GET"])
def whatsapp_webhook():
    # Se alguém fizer GET (checagem), responda OK
    if request.method == "GET":
        return Response('<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
                        mimetype="application/xml", status=200)

    # Twilio envia application/x-www-form-urlencoded
    from_number = request.form.get("From", "")
    body        = request.form.get("Body", "")
    num_media   = int(request.form.get("NumMedia", "0"))
    media_url0  = request.form.get("MediaUrl0") if num_media > 0 else None

    print("---- INBOUND ----")
    print(f"From: {from_number}")
    print(f"Body: {body}")
    print(f"NumMedia: {num_media} | MediaUrl0: {media_url0}")
    print("------------------")

    # Monte a mensagem de retorno (curta e direta)
    if body:
        reply_text = f"✅ Recebi: {body[:120]}"
    elif media_url0:
        reply_text = "📎 Recebi sua mídia! (vou processar)."
    else:
        reply_text = "✅ Recebi sua mensagem!"

    # >>> Resposta via TwiML (o Twilio envia essa mensagem imediatamente) <<<
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Message>{reply_text}</Message>
</Response>'''
    return Response(xml, mimetype="application/xml", status=200)

# (Opcional) status callback não é necessário para TwiML puro, então removi
# Se quiser, mantenha um endpoint de status para futura resposta via API:
# @app.route("/twilio/status", methods=["POST"])
# def twilio_status():
#     msid  = request.form.get("MessageSid")
#     stat  = request.form.get("MessageStatus")
#     err   = request.form.get("ErrorCode")
#     to    = request.form.get("To")
#     from_ = request.form.get("From")
#     print("---- STATUS CALLBACK ----")
#     print(f"Sid: {msid} | Status: {stat} | Error: {err} | To: {to} | From: {from_}")
#     print("-------------------------")
#     return Response('<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
#                     mimetype="application/xml", status=200)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
