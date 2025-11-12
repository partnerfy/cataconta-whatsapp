# app.py
import os
import threading
import re
from flask import Flask, request, jsonify, Response
from twilio.rest import Client

app = Flask(__name__)

# === Variáveis de ambiente (configure no Render > Environment) ===
# - TWILIO_ACCOUNT_SID (Dashboard da Twilio)
# - TWILIO_AUTH_TOKEN
# - TWILIO_WHATSAPP_FROM = whatsapp:+14155238886   # número do Sandbox
# - STATUS_CALLBACK_URL = https://seuapp.onrender.com/twilio/status

TWILIO_SID   = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM  = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
STATUS_CALLBACK = os.environ.get("STATUS_CALLBACK_URL", "")

# Cria o cliente Twilio (se houver credenciais)
client = Client(TWILIO_SID, TWILIO_TOKEN) if (TWILIO_SID and TWILIO_TOKEN) else None


# ---------------------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------------------
def normalize_whatsapp_br(to_number: str) -> str:
    """
    Se for número BR (+55) e vier sem o '9' após o DDD (somente 8 dígitos no final),
    insere o '9' automaticamente.
    Ex.: whatsapp:+554112345678 -> whatsapp:+55411912345678
    """
    m = re.fullmatch(r'whatsapp:\+55(\d{2})(\d{8})', to_number)
    if m:
        ddd, base = m.groups()
        fixed = f"whatsapp:+55{ddd}9{base}"
        print(f"[NORMALIZE] Corrigido número BR: {to_number} -> {fixed}")
        return fixed
    return to_number


def _send_whatsapp(to_number: str, text: str):
    """Envia mensagem via API da Twilio em thread separada."""
    if not client or not to_number or not to_number.startswith("whatsapp:"):
        print("[TWILIO SKIP] client ausente ou 'to' inválido:", to_number)
        return
    try:
        to_number = normalize_whatsapp_br(to_number)
        msg = client.messages.create(
            from_=TWILIO_FROM,
            to=to_number,
            body=text,
            status_callback=STATUS_CALLBACK or None
        )
        print(f"[TWILIO OK] sid={msg.sid} -> Enviando para {to_number}")
    except Exception as e:
        print(f"[TWILIO ERROR] {e}")


# ---------------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    """Usado pelo Render para ver se o app está vivo."""
    return jsonify(ok=True)


@app.route("/", methods=["GET"])
def home():
    return "CataConta WhatsApp Webhook ativo!"


@app.route("/whatsapp/webhook", methods=["POST"])
def whatsapp_webhook():
    """
    Webhook que o Twilio chama sempre que uma mensagem chega no Sandbox.
    Lê o texto, envia uma resposta via API e devolve TwiML vazio (XML) para o Twilio.
    """
    from_number = request.form.get("From", "")       # ex.: 'whatsapp:+55...'
    body        = request.form.get("Body", "")       # texto da mensagem
    num_media   = int(request.form.get("NumMedia", "0"))
    media_url0  = request.form.get("MediaUrl0") if num_media > 0 else None

    print("---- INBOUND ----")
    print(f"From: {from_number}")
    print(f"Body: {body}")
    print(f"NumMedia: {num_media} | MediaUrl0: {media_url0}")
    print("------------------")

    # Mensagem simples de confirmação
    if body:
        reply_text = f"✅ Recebi: {body[:120]}"
    elif media_url0:
        reply_text = "📎 Recebi sua mídia! (vou processar)."
    else:
        reply_text = "✅ Recebi sua mensagem!"

    # Envia a resposta ao usuário via API (thread separada)
    if from_number:
        threading.Thread(
            target=_send_whatsapp,
            args=(from_number, reply_text),
            daemon=True
        ).start()

    # Retorna TwiML vazio (XML) para evitar erro 12300
    return Response(
        '<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
        mimetype="application/xml",
        status=200
    )


@app.route("/twilio/status", methods=["POST"])
def twilio_status():
    """
    Endpoint de callback de status das mensagens enviadas.
    Mostra status de entrega (queued, sent, delivered, undelivered, failed)
    e o código de erro (ex.: 63016 = número não fez join).
    """
    msid  = request.form.get("MessageSid")
    stat  = request.form.get("MessageStatus")
    err   = request.form.get("ErrorCode")
    to    = request.form.get("To")
    from_ = request.form.get("From")

    print("---- STATUS CALLBACK ----")
    print(f"Sid: {msid} | Status: {stat} | Error: {err} | To: {to} | From: {from_}")
    print("-------------------------")

    return Response(
        '<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
        mimetype="application/xml",
        status=200
    )


# ---------------------------------------------------------------
# EXECUÇÃO LOCAL (para testes)
# ---------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
