from langchain.document_loaders import PyPDFLoader , DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import os
load_dotenv()


from src.helper import download_embeddings, filter_to_minimal_docs, load_pdf_files, text_split


data_path = "/Users/gunjeshnayak/Desktop/AI_ChatBot/HealthAIChatBot/Data"
extracted_files = load_pdf_files(data_path)

minimal_docs = filter_to_minimal_docs(extracted_files)

texts_chunk = text_split(minimal_docs)

embeddings = download_embeddings()

PINECONE_API_KEY=os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"]=OPENAI_API_KEY
os.environ["PINECONE_API_KEY"]=PINECONE_API_KEY


from pinecone import Pinecone # This class is available in 7.x
from langchain_pinecone import PineconeVectorStore
# ... your code
pinecone_api_key=PINECONE_API_KEY

# Initialize a Pinecone client with your API key
pc = Pinecone(api_key=pinecone_api_key)


from pinecone import ServerlessSpec

index_name = "health-ai-chatbot-index"

if pc is None:
    # Pinecone unavailable (bad key or init failed). Skip remote index creation.
    print("Pinecone client not available; skipping remote index creation. Use a local vectorstore fallback if needed.")
    index = None
else:
    try:
        if not pc.has_index(index_name):
            pc.create_index(
                name=index_name,
                dimension=384,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws", region="us-east-1",
                ),
            )
        index = pc.Index(index_name)
    except Exception as e:
        print("Failed to create or access Pinecone index:", e)
        index = None
        
        
        
from langchain_pinecone import PineconeVectorStore
doc_search = PineconeVectorStore.from_documents(
    documents=texts_chunk,
    index_name=index_name,
    embedding=embeddings
)

#load existing index
from langchain_pinecone import PineconeVectorStore
doc_search = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings
)