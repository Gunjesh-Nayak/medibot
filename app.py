import os
import logging
import threading
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Import modules
from src.brain import init_medical_bot, get_ai_response
from src.whatsapp import parse_incoming_message, process_text, send_message, get_text_message_input

load_dotenv()
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
medical_brain = init_medical_bot()

def background_process(body):
    with app.app_context():
        # 1. Parse - This will now return None for status updates
        data = parse_incoming_message(body)
        if not data:
            # logging.info("Ignored status update or non-text message")
            return 

        logging.info(f"Processing query from {data['name']}: {data['body']}")

        # 2. Think
        raw_answer = get_ai_response(medical_brain, data['body'])

        # 3. Reply
        clean_answer = process_text(raw_answer)
        payload = get_text_message_input(data['wa_id'], clean_answer)
        send_message(payload)

@app.route("/", methods=["GET"])
def index():
    return "MediBot is Running!", 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Forbidden", 403

    if request.method == "POST":
        body = request.get_json()
        if body.get("object"):
            # Threading prevents "Timeout" errors
            thread = threading.Thread(target=background_process, args=(body,))
            thread.start()
        return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1205, debug=True)