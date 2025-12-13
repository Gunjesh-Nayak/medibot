from langchain.document_loaders import PyPDFLoader , DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pinecone import Pinecone # This class is available in 7.x
from langchain_pinecone import PineconeVectorStore
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate


#extracting text from pdfs in a directory
def load_pdf_files(data):
    loader = DirectoryLoader(
        data,  # Fixed: using the parameter name 'data' instead of 'Data'
        glob="*.pdf", 
        loader_cls=PyPDFLoader)
    documents=loader.load()
    return documents


# filtering documents to a maximum number
from typing import List
from langchain.schema import Document
def filter_to_minimal_docs(docs: List[Document]) -> List[Document]:
    """Filter the list of documents to a maximum number."""
    minimal_docs: List[Document] = []
    for doc in docs:
        src = doc.metadata.get("source")
        minimal_docs.append(
            Document(
                page_content=doc.page_content,
                metadata={"source": src} if src else {},
            )
        )
    return minimal_docs

#splitting the documents into smaller chunks
def text_split(minimal_docs):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=20,
    )
    texts_chunk = text_splitter.split_documents(minimal_docs)
    return texts_chunk

# downloading the embeddings model
from langchain.embeddings import HuggingFaceEmbeddings
import torch

def download_embeddings():
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2",
                                        model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"})
    return embeddings

embeddings = download_embeddings()


