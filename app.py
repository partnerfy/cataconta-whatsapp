# app.py
import os
import threading
from flask import Flask, request, jsonify, Response
from twilio.rest import Client

app = Flask(__name__)

# === Variáveis de ambiente (configure no Render > Environment) ===
# - TWILIO_ACCOUNT_SID (Dashboard da Twilio)
# - TWILIO_AUTH_TOKEN
# - TWILIO_WHATSAPP_FROM = whatsapp:+14155238886   # número do Sandbox
TWILIO_SID   = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM  = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

# Cria o cliente Twilio apenas se as credenciais existirem
client = Client(TWILIO_SID, TWILIO_TOKEN) if (TWILIO_SID and TWILIO_TOKEN) else None


@app.route("/health", methods=["GET"])
def health():
    """Endpoint simples para checagem/keep-alive"""
    return jsonify(ok=True)


@app.route("/", methods=["GET"])
def home():
    return "CataConta WhatsApp Webhook ativo!"


def _send_whatsapp(to_number: str, text: str):
    """Envia mensagem via API da Twilio em thread separada"""
    if not client or not to_number or not to_number.startswith("whatsapp:"):
        print("[TWILIO SKIP] client ausente ou 'to' inválido:", to_number)
        return
    try:
        msg = client.messages.create(
            from_=TWILIO_FROM,   # sandbox
            to=to_number,        # quem enviou
            body=text
        )
        print(f"[TWILIO OK] sid={msg.sid}")
    except Exception as e:
        print(f"[TWILIO ERROR] {e}")


@app.route("/whatsapp/webhook", methods=["POST"])
def whatsapp_webhook():
    """
    Webhook que o Twilio chama a cada mensagem recebida no Sandbox.
    - Lê dados do formulário (x-www-form-urlencoded).
    - Dispara a resposta via API da Twilio (thread).
    - Retorna TwiML vazio (application/xml) para satisfazer o Twilio (evita 12300).
    """
    # Twilio envia application/x-www-form-urlencoded
    from_number = request.form.get("From", "")       # ex.: 'whatsapp:+55...'
    body        = request.form.get("Body", "")       # texto da mensagem
    num_media   = int(request.form.get("NumMedia", "0"))
    media_url0  = request.form.get("MediaUrl0") if num_media > 0 else None

    print("---- INBOUND ----")
    print(f"From: {from_number}")
    print(f"Body: {body}")
    print(f"NumMedia: {num_media} | MediaUrl0: {media_url0}")
    print("------------------")

    # Mensagem de retorno simples
    if body:
        reply_text = f"✅ Recebi: {body[:120]}"
    elif media_url0:
        reply_text = "📎 Recebi sua mídia! (vou processar)."
    else:
        reply_text = "✅ Recebi sua mensagem!"

    # Envia a resposta ao usuário via API (sem bloquear o webhook)
    if from_number:
        threading.Thread(
            target=_send_whatsapp,
            args=(from_number, reply_text),
            daemon=True
        ).start()

    # >>> FIX do erro 12300: devolver TwiML/XML válido para o Twilio <<<
    return Response(
        '<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
        mimetype="application/xml",
        status=200
    )


# Para rodar LOCALMENTE (não usado no Render quando Start Command for gunicorn)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # Em local dev, pode ser app.run; em produção use gunicorn (ver comando abaixo).
    app.run(host="0.0.0.0", port=port, debug=True)
