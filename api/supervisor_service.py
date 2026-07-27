from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from .langgraph_service import run_langgraph_rag

def classify_intent(query:str)-> str:
    llm = ChatGroq(model ="llama-3.3-70b-versatile", temperature=0)
    prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are the Master Intent Classifier for an Enterprise Knowledge Base.

              Classify the user's input into EXACTLY ONE category:

              1. CODE: Use ONLY if the user explicitly requests to write, debug, refactor, or explain programming code/scripts.
              2. GENERAL: Use ONLY for simple greetings (e.g. "hi", "hello", "hey"), casual small talk, or farewells.
              3. RAG: Use for ALL OTHER QUESTIONS! Any factual query, name inquiry, entity lookup, document question, summary, or information search MUST be classified as RAG so the system searches the uploaded knowledge base.

            Return ONLY one word:
            RAG
            CODE
            GENERAL
            """
        ),("human", "{question}")])

    chain = prompt|llm
    response = chain.invoke({"question": query}) 
    return response.content.strip().upper()


def route_and_execute(query:str,user_id:int = 1):
    llm = ChatGroq(model ="llama-3.3-70b-versatile", temperature=0)
    intent = classify_intent(query)
    result = run_langgraph_rag(query, user_id=user_id)
    if intent == "RAG":
         return run_langgraph_rag(query, user_id=user_id)
    elif intent == "CODE":
        code_response = llm.invoke(query)
        return {"query": query, "intent": "CODE", "answer": code_response.content}
    else :
        return {"query": query, "intent": "GENERAL", "answer": "Hello! How can I assist you today?"} 

