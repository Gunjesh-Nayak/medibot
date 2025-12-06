import os
import requests
import json
import re
import logging
from flask import current_app

def get_text_message_input(recipient, text):
    return json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "text",
        "text": {"preview_url": False, "body": text}
    })

def send_message(data):
    # Retrieve tokens from Environment Variables or Flask Config
    token = os.getenv("ACCESS_TOKEN")
    phone_id = os.getenv("PHONE_NUMBER_ID")
    
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    url = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
    
    try:
        response = requests.post(url, data=data, headers=headers, timeout=10)
        response.raise_for_status()
        return response
    except Exception as e:
        logging.error(f"Error sending WhatsApp message: {e}")
        return None

def process_text(text):
    # Clean up RAG references like 【source】 and fix bolding
    text = re.sub(r"\【.*?\】", "", text).strip()
    text = re.sub(r"\*\*(.*?)\*\*", r"*\1*", text)
    return text

def parse_incoming_message(body):
    """
    Extracts the user's number and message from the webhook data.
    Returns None if the data is invalid.
    """
    try:
        entry = body["entry"][0]["changes"][0]["value"]
        message = entry["messages"][0]
        
        # Only handle text messages
        if message.get("type") != "text":
            return None
            
        return {
            "wa_id": message["from"],
            "name": entry["contacts"][0]["profile"]["name"],
            "body": message["text"]["body"]
        }
    except (KeyError, IndexError):
        return None