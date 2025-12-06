import os
import requests
import json
import re
import logging

def get_text_message_input(recipient, text):
    return json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "text",
        "text": {"preview_url": False, "body": text}
    })

def send_message(data):
    token = os.getenv("ACCESS_TOKEN")
    phone_id = os.getenv("PHONE_NUMBER_ID")
    version = os.getenv("VERSION", "v17.0")
    
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    url = f"https://graph.facebook.com/{version}/{phone_id}/messages"
    
    try:
        response = requests.post(url, data=data, headers=headers, timeout=10)
        response.raise_for_status()
        return response
    except Exception as e:
        logging.error(f"Error sending WhatsApp message: {e}")
        return None

def process_text(text):
    text = re.sub(r"\【.*?\】", "", text).strip()
    text = re.sub(r"\*\*(.*?)\*\*", r"*\1*", text)
    return text

def parse_incoming_message(body):
    """
    Extracts the user's number and message.
    CRITICAL FIX: Returns None if the webhook is a 'status' update.
    """
    try:
        # 1. Check if this is a Status Update (sent/delivered/read)
        # If 'statuses' exists, it's NOT a message. Ignore it.
        entry = body["entry"][0]["changes"][0]["value"]
        if "statuses" in entry:
            return None

        # 2. Check if it is a Message
        if "messages" not in entry:
            return None

        message = entry["messages"][0]
        
        # 3. Only handle text messages
        if message.get("type") != "text":
            return None
            
        return {
            "wa_id": message["from"],
            "name": entry["contacts"][0]["profile"]["name"],
            "body": message["text"]["body"]
        }
    except (KeyError, IndexError):
        # If the structure is weird, ignore it rather than crashing
        return None