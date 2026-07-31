import os
from typing import Dict, Any, List
from dotenv import load_dotenv

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader, CSVLoader, TextLoader
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_groq import ChatGroq

load_dotenv()

# Global Embedding Engine & In-Memory Vector Store Initialization
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
vector_store = InMemoryVectorStore(embeddings)


def load_document(directory: str, user_id: int = 1) -> Dict[str, Any]:
    """
    Scans a directory for supported files (.pdf, .txt, .md, .csv), splits text into 
    overlapping chunks, attaches user_id metadata for multi-tenancy, and indexes 
    them into the vector database.
    """
    if not os.path.exists(directory):
        return {"error": f"Directory '{directory}' does not exist"}

    document = []
    for filename in os.listdir(directory):
        path = os.path.join(directory, filename)
        if filename.endswith(".md") or filename.endswith(".txt"):
            loader = TextLoader(path, encoding='utf-8')
            document.extend(loader.load())
        elif filename.endswith(".csv"):
            loader = CSVLoader(path, encoding='utf-8')
            document.extend(loader.load())
        elif filename.endswith(".pdf"):
            loader = PyPDFLoader(path)
            document.extend(loader.load())

    if not document:
        return {"error": "No supported documents found in target path"}

    # Recursive text splitting with context overlap
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(document)

    # Attach user_id to metadata for strict multi-tenant isolation
    for chunk in chunks:
        chunk.metadata["user_id"] = user_id

    # Embed and index chunks into vector store
    vector_store.add_documents(chunks)

    return {
        "directory": directory,
        "user_id": user_id,
        "total_documents": len(document),
        "total_chunks": len(chunks),
        "chunks": chunks
    }


def query_rag(query: str, user_id: int = 1, top_k: int = 3) -> List[Any]:
    """
    Performs similarity search against the vector index with strict user_id metadata filtering.
    """
    search_results = vector_store.similarity_search(
        query, 
        k=top_k, 
        filter=lambda doc: doc.metadata.get("user_id") == user_id
    )
    return search_results


def generate_rag_answer(query: str, user_id: int = 1) -> Dict[str, Any]:
    """
    Retrieves user-scoped context chunks, constructs a grounded RAG prompt, 
    and generates an LLM response with source file citations.
    """
    docs = query_rag(query, user_id=user_id, top_k=3)
    if not docs:
        return {
            "query": query,
            "answer": "No relevant document found for your query",
            "sources": [],
            "chunks_retrieved": 0
        }

    context = "\n\n".join([doc.page_content for doc in docs])
    sources = list(set([doc.metadata.get("source", "Unknown") for doc in docs]))

    prompt = f"Answer the question based ONLY on the provided context.\n\nContext:\n{context}\n\nQuestion: {query}\nAnswer:"
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
    response = llm.invoke(prompt)

    return {
        "query": query,
        "answer": response.content,
        "sources": sources,
        "chunks_retrieved": len(docs)
    }
