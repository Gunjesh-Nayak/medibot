import os
import logging
import json
import re
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# --- PROJECT IMPORTS ---
# Ensure these files exist in your 'src' folder
# Removed 'create_app' to avoid circular imports
from src.helper import download_embeddings
from src.prompt import system_prompt

# --- LANGCHAIN IMPORTS ---
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# --- 1. CONFIGURATION ---
load_dotenv()
# Initialize Flask directly to avoid circular imports from src/__init__.py
app = Flask(__name__)

# Load API Keys
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")     # WhatsApp Token
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")     # Custom password for Meta

# Set Environment Variables for LangChain
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY

# Setup Logging (To see what's happening in terminal)
logging.basicConfig(level=logging.INFO)


# --- 2. INITIALIZE THE BRAIN (AI) ---
app.logger.info("Initializing Medical AI...")

embeddings = download_embeddings()
index_name = "health-ai-chatbot-index"

# Connect to Pinecone
doc_search = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings
)
retriever = doc_search.as_retriever(search_kwargs={"k": 3}, search_type="similarity")

# FIXED: Changed 'gpt-5-nano' (invalid) to 'gpt-3.5-turbo'
chatmodel = ChatOpenAI(model_name="gpt-3.5-turbo") 

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "context: {context}\n\nQuestion: {input}"),
])
question_answering_chain = create_stuff_documents_chain(chatmodel, prompt)
rag_chain = create_retrieval_chain(retriever, question_answering_chain)

app.logger.info("AI Ready!")


# --- 3. WHATSAPP HELPER FUNCTIONS ---

def send_whatsapp_message(recipient, text):
    """Sends the text back to the user"""
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"preview_url": False, "body": text}
    }
    try:
        r = requests.post(url, headers=headers, json=data)
        r.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to send message: {e}")

def process_text(text):
    """Cleans up bold text for WhatsApp"""
    text = re.sub(r"\【.*?\】", "", text).strip()
    text = re.sub(r"\*\*(.*?)\*\*", r"*\1*", text) 
    return text

def handle_incoming_message(body):
    """The Logic Flow: Receive -> Think -> Reply"""
    try:
        # 1. Extract Data
        entry = body["entry"][0]["changes"][0]["value"]
        message = entry["messages"][0]
        wa_id = message["from"]  # SENDER'S NUMBER (Critical Fix)
        user_msg = message["text"]["body"]
        name = entry["contacts"][0]["profile"]["name"]

        logging.info(f"Msg from {name}: {user_msg}")

        # 2. Ask the Brain (RAG Chain)
        response = rag_chain.invoke({"input": user_msg})
        ai_answer = response["answer"]

        # 3. Speak (Send Reply)
        clean_answer = process_text(ai_answer)
        send_whatsapp_message(wa_id, clean_answer)

    except Exception as e:
        logging.error(f"Error handling message: {e}")


# --- 4. FLASK ROUTES ---

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # VERIFICATION (GET)
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Forbidden", 403

    # MESSAGES (POST)
    if request.method == "POST":
        body = request.get_json()
        
        # Check if it's a valid message (not a status update)
        if body.get("object") and \
           body.get("entry") and \
           "messages" in body["entry"][0]["changes"][0]["value"]:
            
            handle_incoming_message(body)
            
        return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1205, debug=True)