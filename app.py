# app.py
from flask import Flask, request, Response

app = Flask(__name__)

@app.route("/whatsapp/webhook", methods=["POST"])
def whatsapp_webhook():
    from_number = request.form.get("From")
    body = request.form.get("Body")
    print(f"Mensagem recebida de {from_number}: {body}")

    # resposta automática simples
    reply = "<Response><Message>✅ Recebi sua mensagem!</Message></Response>"
    return Response(reply, mimetype="text/xml")

@app.route("/")
def home():
    return "CataConta WhatsApp Webhook ativo!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
