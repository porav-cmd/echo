import os
from typing import List, Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from .rag_service import query_rag


class RagState(TypedDict):
    """
    Central state container passed between nodes in the LangGraph RAG pipeline.
    """
    question: str
    user_id: int
    documents: List[str]
    sources: List[str]
    answer: str


def retrieve_node(state: RagState) -> Dict[str, Any]:
    """
    Node 1: Retrieves documents from vector store filtered strictly by user_id.
    """
    question = state["question"]
    user_id = state["user_id"]
    retrieved_docs = query_rag(question, user_id=user_id)
    
    docs = [d.page_content for d in retrieved_docs]
    sources = list(set([d.metadata.get("source", "Unknown") for d in retrieved_docs]))
    
    return {"documents": docs, "sources": sources}


def generate_code_node(state: RagState) -> Dict[str, Any]:
    """
    Node 2: Generates a grounded response using retrieved documents and LCEL prompt chain.
    """
    groq_api_key = os.getenv("GROQ_API_KEY", "placeholder")
    try:
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2, groq_api_key=groq_api_key)
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are a helpful Enterprise AI Assistant.
                Use ONLY the provided retrieved documents to answer the user's question accurately.

                Instructions:
                 - Base your answer entirely on the provided context.
                 - Do not use ungrounded outside knowledge.
                 - If the answer cannot be found in the context, say "No relevant document found for your query."
                 - Be clear, concise, and structured.
                """
            ),
            (
                "human",
                "Question: {question}\n\nRetrieved Documents:\n{documents}"
            ),
        ])

        chain = prompt | llm
        formatted_docs = "\n\n".join(state["documents"])
        response = chain.invoke({"question": state["question"], "documents": formatted_docs})
        
        return {"answer": response.content}
    except Exception as e:
        print(f"Langgraph node notice: {e}")
        return {"answer": "No relevant document found for your query."}


def fallback_node(state: RagState) -> Dict[str, Any]:
    """
    Node 3: Fallback node executed when retrieved documents are empty or irrelevant.
    """
    return {
        "answer": "No relevant document found for your query",
        "sources": []
    }


def should_generate(state: RagState) -> str:
    """
    Conditional Edge Evaluator: Inspects retrieved documents and routes to 
    'generate' if context exists, or 'fallback' if empty.
    """
    if state["documents"]:
        return "generate"
    return "fallback"


# Construct LangGraph State Graph
workflow = StateGraph(RagState)

# Add Nodes
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate_code_node)
workflow.add_node("fallback", fallback_node)

# Add Edges & Conditional Routing
workflow.set_entry_point("retrieve")
workflow.add_conditional_edges(
    "retrieve",
    should_generate,
    {
        "generate": "generate",
        "fallback": "fallback"
    }
)
workflow.add_edge("generate", END)
workflow.add_edge("fallback", END)

# Compile LangGraph Pipeline
app_graph = workflow.compile()


def run_langgraph_rag(query: str, user_id: int = 1) -> Dict[str, Any]:
    """
    Invokes the compiled LangGraph pipeline for stateful, graph-managed RAG execution.
    """
    initial_state = {
        "question": query,
        "user_id": user_id,
        "documents": [],
        "sources": [],
        "answer": ""
    }

    final_state = app_graph.invoke(initial_state)

    return {
        "query": query,
        "answer": final_state.get("answer", "No answer generated"),
        "sources": final_state.get("sources", []),
        "chunks_retrieved": len(final_state.get("documents", []))
    }