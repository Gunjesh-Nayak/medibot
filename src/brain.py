import os
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from src.helper import download_embeddings
from src.prompt import system_prompt

def init_medical_bot():
    """Initializes and returns the RAG chain"""
    print("Loading Medical AI Brain...")
    
    embeddings = download_embeddings()
    index_name = "health-ai-chatbot-index"

    doc_search = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embeddings
    )
    retriever = doc_search.as_retriever(search_kwargs={"k": 3}, search_type="similarity")

    chatmodel = ChatOpenAI(model_name="gpt-3.5-turbo")

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "context: {context}\n\nQuestion: {input}"),
    ])
    
    question_answering_chain = create_stuff_documents_chain(chatmodel, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answering_chain)
    
    print("Medical AI Brain Ready!")
    return rag_chain

def get_ai_response(rag_chain, user_input):
    """Asks the RAG chain a question"""
    try:
        response = rag_chain.invoke({"input": user_input})
        return response["answer"]
    except Exception as e:
        return "I apologize, but I am having trouble processing that medical query right now."