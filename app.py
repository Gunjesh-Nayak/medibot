# app.py

from flask import Flask, logging, render_template, jsonify, request

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

# from flask import Flask

# from start.whatsapp_quickstart import get_text_message_input

app = create_app()
# app = Flask(__name__)
load_dotenv()
PINECONE_API_KEY=os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"]=OPENAI_API_KEY
os.environ["PINECONE_API_KEY"]=PINECONE_API_KEY

embeddings = download_embeddings()

index_name = "health-ai-chatbot-index"

doc_search = PineconeVectorStore.from_existing_index(
    # documents=texts_chunk,
    index_name=index_name,
    embedding=embeddings
)

retriever = doc_search.as_retriever(search_kwargs={"k": 3}, search_type="similarity")

chatmodel = ChatOpenAI(model_name="gpt-5-nano")

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "context: {context}\n\nQuestion: {input}"),
])
question_answering_chain = create_stuff_documents_chain(chatmodel, prompt)

# create a retrieval-augmented generation chain using the retriever and the Q/A chain
rag_chain = create_retrieval_chain(
    
retriever,
    question_answering_chain
)

@app.route("/webhook", methods=["POST","GET"])
def chat():
    msg=request.get_json()
    input =msg
    print(input)
    response = rag_chain.invoke({"input":msg})
    print("response:",response["answer"])
    
   

# @app.route("/webhook")
# def chat():
#     return "helloworld"


if __name__ == "__main__":
    app.logger.info("Starting Flask app...")
    app.run(host="0.0.0.0", port=1205, debug=False) 