from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from .langgraph_service import run_langgraph_rag


def classify_intent(query: str) -> str:
    """
    Classifies user query into 'RAG', 'CODE', or 'GENERAL' using Groq LLM.
    Defaults to 'RAG' for any factual, document, name, or domain query.
    """
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    prompt = ChatPromptTemplate.from_messages([
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
        ),
        ("human", "{question}")
    ])

    chain = prompt | llm
    response = chain.invoke({"question": query})
    return response.content.strip().upper()


def route_and_execute(query: str, user_id: int = 1) -> Dict[str, Any]:
    """
    Multi-Agent Supervisor Router: Inspects classified intent and dispatches 
    the request to the appropriate specialized worker node (RAG, CODE, or GENERAL).
    """
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
    intent = classify_intent(query)

    if "RAG" in intent:
        rag_result = run_langgraph_rag(query, user_id=user_id)
        rag_result["intent"] = "RAG"
        return rag_result

    elif "CODE" in intent:
        code_prompt = f"Write clean, efficient, and well-commented code for the following request:\n\nRequest: {query}"
        code_response = llm.invoke(code_prompt)
        return {
            "query": query,
            "intent": "CODE",
            "answer": code_response.content,
            "user_id": user_id
        }

    else:
        general_prompt = f"Provide a helpful, friendly, and concise response to:\n\nUser: {query}"
        general_response = llm.invoke(general_prompt)
        return {
            "query": query,
            "intent": "GENERAL",
            "answer": general_response.content,
            "user_id": user_id
        }
