# app.py
import os
import re
from flask import Flask, request, jsonify, Response
from twilio.rest import Client

app = Flask(__name__)

# === Variáveis de ambiente (Render > Environment) ===
# - TWILIO_ACCOUNT_SID  (começa com AC...)
# - TWILIO_AUTH_TOKEN
# - TWILIO_WHATSAPP_FROM = whatsapp:+14155238886   # número do Sandbox
# - STATUS_CALLBACK_URL = https://SEUAPP.onrender.com/twilio/status  (opcional)
TWILIO_SID        = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN      = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM       = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
STATUS_CALLBACK   = os.environ.get("STATUS_CALLBACK_URL", "")

# Cria o cliente Twilio se houver credenciais
client = Client(TWILIO_SID, TWILIO_TOKEN) if (TWILIO_SID and TWILIO_TOKEN) else None


# ---------------------------------------------------------------
# AUXILIARES
# ---------------------------------------------------------------
def normalize_whatsapp_br(to_number: str) -> str:
    """
    Se for BR (+55) e vier sem o '9' após o DDD (apenas 8 dígitos),
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
    """Envio SÍNCRONO (diagnóstico): loga tudo e dispara a mensagem via API."""
    print(f"[DIAG] TWILIO_SID set? {bool(TWILIO_SID)}  "
          f"TWILIO_TOKEN set? {bool(TWILIO_TOKEN)}  FROM={TWILIO_FROM}")
    if not client:
        print("[TWILIO SKIP] client ausente (credenciais não configuradas?)")
        return
    if not to_number or not to_number.startswith("whatsapp:"):
        print(f"[TWILIO SKIP] 'to' inválido: {to_number}")
        return
    try:
        to_number = normalize_whatsapp_br(to_number)
        print(f"[DIAG] Enviando via API: from={TWILIO_FROM} to={to_number} body='{text}'")
        msg = client.messages.create(
            from_=TWILIO_FROM,
            to=to_number,
            body=text,
            status_callback=STATUS_CALLBACK or None
        )
        print(f"[TWILIO OK] sid={msg.sid}")
    except Exception as e:
        import traceback
        print("[TWILIO ERROR] Exception ao criar mensagem:")
        traceback.print_exc()


# ---------------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    """Keep-alive/healthcheck."""
    return jsonify(ok=True)


@app.route("/", methods=["GET"])
def home():
    return "CataConta WhatsApp Webhook ativo!"


@app.route("/whatsapp/webhook", methods=["POST", "GET"])
def whatsapp_webhook():
    """
    Webhook chamado pelo Twilio a cada mensagem recebida no Sandbox.
    - Lê o formulário (x-www-form-urlencoded)
    - Envia a resposta SÍNCRONA via API Twilio (com logs detalhados)
    - Retorna TwiML vazio (XML) para satisfazer o Twilio (evita 12300)
    """
    if request.method == "GET":
        # Algumas checagens/bots podem fazer GET: devolva TwiML vazio
        return Response('<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
                        mimetype="application/xml", status=200)

    from_number = request.form.get("From", "")       # ex.: 'whatsapp:+55...'
    body        = request.form.get("Body", "")       # texto
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

    # >>> Envio SÍNCRONO para garantir logs imediatos do que está acontecendo
    if from_number:
        _send_whatsapp(from_number, reply_text)

    # TwiML vazio (XML) para o Twilio ficar satisfeito
    return Response(
        '<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
        mimetype="application/xml",
        status=200
    )


@app.route("/twilio/status", methods=["POST"])
def twilio_status():
    """
    Callback de status de entrega.
    Mostra: queued, sent, delivered, undelivered, failed + ErrorCode (ex.: 63016).
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
# Em produção (Render), use GUNICORN:
#   gunicorn app:app -w 2 -k gthread -b 0.0.0.0:$PORT --timeout 30
# ---------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
