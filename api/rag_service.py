import os
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader,CSVLoader,TextLoader
from langchain_core.vectorstores import InMemoryVectorStore 
from langchain_groq import ChatGroq


load_dotenv()
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2",output_dimensionality=1024)
vector_store = InMemoryVectorStore(embeddings)

def load_document(directory,user_id=1):
    if not os.path.exists(directory):
        return {"error": f"Directory '{directory}' does not exist"}
    document = []
    for filename in os.listdir(directory):
        path = os.path.join(directory,filename)
        if  filename.endswith(".md"):
            loader = TextLoader(path)
            document.extend(loader.load())
        elif filename.endswith(".csv"):
            loader = CSVLoader(path)
            document.extend(loader.load())
        elif filename.endswith(".pdf"):
            loader = PyPDFLoader(path)
            document.extend(loader.load())

    if not document:
         return {"error": "No supported documents found"} 

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(document)   

    for chunk in chunks:
        chunk.metadata["user_id"] = user_id

    vector_store.add_documents(chunks)    

    return {"directory": directory,"user_id": user_id,"total_documents": len(document),"total_chunks": len(chunks),"chunks": chunks}


def query_rag(query, user_id = 1 , top_k = 3):
    search = vector_store.similarity_search(query, k=top_k, filter=lambda doc: doc.metadata.get("user_id") == user_id)
    return search   



def generate_rag_answer(query,user_id=1):
    docs = query_rag(query,user_id=user_id,top_k=3)
    if not docs:
        return{"answer": "No relevant documents found for your query.", "sources": []}
    context = "\n\n".join([doc.page_content for doc in docs])    
    sources = list(set([doc.metadata.get("source","unkown")for doc in docs]))
    prompt = f"Answer the question based only on the following.\n\nContext:\n{context}\n\nQuestion:{query}\nAnswer"
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    response = llm.invoke(prompt)
    return {"query":query,
             "answer":response.content,
             "sources":sources,
             "chunks_retrievel":len(docs)}
