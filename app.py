from flask import Flask, render_template, jsonify, request
from src import create_app
from src.helper import download_embeddings
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from src.prompt import *
import os

# Load environment variables
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Initialize App
app = create_app()
# app = Flask(__name__)

# Load Embeddings
embeddings = download_embeddings()

# Connect to Pinecone
index_name = "health-ai-chatbot-index"

# Ensure your Pinecone index matches the dimension of your embeddings 
# (384 for all-MiniLM-L6-v2, 1536 for OpenAI embeddings)
doc_search = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings
)

retriever = doc_search.as_retriever(search_kwargs={"k": 3}, search_type="similarity")

# FIX 1: Use a valid model name (gpt-3.5-turbo or gpt-4o-mini)
chatmodel = ChatOpenAI(model_name="gpt-5-nano")

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "context: {context}\n\nQuestion: {input}"),
])

question_answering_chain = create_stuff_documents_chain(chatmodel, prompt)

rag_chain = create_retrieval_chain(
    retriever,
    question_answering_chain
)

@app.route("/")
def index():
    return "MediBot is Running!"

@app.route("/webhook", methods=["POST"])
def chat():
    try:
        # Get JSON data
        msg_data = request.get_json()
        
        # FIX 2: Handle input correctly. 
        # Assuming you send JSON like: {"msg": "What is a fever?"}
        # If you are sending raw text, this logic needs to change.
        if not msg_data:
            return jsonify({"error": "No JSON received"}), 400
            
        # Extract the user's message from the JSON key (e.g., 'msg', 'query', or 'message')
        # We will try to find the key, or default to treating the whole body as text if it's not a dict
        if isinstance(msg_data, dict):
            user_input = msg_data.get("msg") or msg_data.get("message")
        else:
            user_input = str(msg_data)

        if not user_input:
            return jsonify({"error": "No message found in JSON. Use key 'msg', 'query', or 'message'"}), 400

        print(f"User Input: {user_input}")

        # Invoke Chain
        response = rag_chain.invoke({"input": user_input})
        
        answer = response["answer"]
        print("Response:", answer)
        
        # FIX 3: Return a valid response to the client
        return jsonify({"answer": answer})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500
    # Add this near your other environment variables
VERIFY_TOKEN = "vibecode"  # <--- IMPORTANT: Set this to whatever you type in the Meta Dashboard

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # 1. HANDLE WHATSAPP VERIFICATION (GET REQUEST)
    if request.method == "GET":
        # Meta sends these parameters to verify your webhook
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        # Check if the token matches what you set in the Meta Dashboard
        if mode and token:
            if mode == "subscribe" and token == VERIFY_TOKEN:
                print("WEBHOOK_VERIFIED")
                return challenge, 200
            else:
                return "Verification token mismatch", 403
        
        return "MediBot Server is Running! (Use POST to chat)", 200

    # 2. HANDLE CHAT MESSAGES (POST REQUEST)
    elif request.method == "POST":
        try:
            data = request.get_json()
            
            # Print data for debugging
            print("Received Data:", data)

            # --- WHATSAPP SPECIFIC EXTRACTION ---
            # If you are using WhatsApp, the message is buried deep in the JSON.
            # We need to extract it safely.
            if data and 'entry' in data:
                changes = data['entry'][0]['changes'][0]
                if 'value' in changes and 'messages' in changes['value']:
                    message = changes['value']['messages'][0]
                    if message['type'] == 'text':
                        user_input = message['text']['body']
                        
                        # --- GENERATE AI RESPONSE ---
                        print(f"User Query: {user_input}")
                        response = rag_chain.invoke({"input": user_input})
                        bot_answer = response["answer"]
                        print(f"Bot Answer: {bot_answer}")
                        
                        # IMPORTANT: You must return 200 OK to WhatsApp 
                        # immediately, otherwise they will keep retrying.
                        # (You usually need a separate function to send the reply back to WhatsApp API)
                        return jsonify({"status": "success", "reply": bot_answer}), 200

            # --- GENERIC/POSTMAN TESTING ---
            # Fallback for when you are just testing with Postman
            elif data and 'msg' in data:
                user_input = data['msg']
                response = rag_chain.invoke({"input": user_input})
                return jsonify({"answer": response["answer"]}), 200

            return jsonify({"status": "ignored", "reason": "Not a text message"}), 200

        except Exception as e:
            print(f"Error: {e}")
            return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1205, debug=False)