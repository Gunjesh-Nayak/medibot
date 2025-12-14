# from flask import Flask, render_template, jsonify, request # REMOVED: Not needed here
from src.helper import download_embeddings
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from src.prompt import *
import os

# 1. Load Config
load_dotenv()
os.environ["PINECONE_API_KEY"] = os.getenv("PINECONE_API_KEY")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# 2. Setup Vector Store
embeddings = download_embeddings()
index_name = "health-ai-chatbot-index"

doc_search = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings
)

retriever = doc_search.as_retriever(search_kwargs={"k": 3}, search_type="similarity")

# 3. Setup LLM & Chain
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

# 4. THE CORRECTED FUNCTION
def generate_response(message_body, wa_id, name):
    """
    Args:
        message_body (str): The plain text question (e.g., "What is fever?")
        wa_id (str): The user's phone number
        name (str): The user's name
    Returns:
        str: The plain text answer from the bot
    """
    print(f"Generating response for Name: {name} ({wa_id})")
    print(f"User Query: {message_body}")

    try:
        # A. Invoke the RAG chain
        # Note: message_body is ALREADY a string here, so we pass it directly.
        response = rag_chain.invoke({"input": message_body})
        
        # B. Extract just the answer string
        bot_answer = response["answer"]
        print(f"Bot Answer: {bot_answer}")
        
        # C. Return just the string (NOT jsonify)
        return bot_answer

    except Exception as e:
        print(f"Error generating response: {e}")
        return "I am having trouble accessing my health database right now. Please try again later."