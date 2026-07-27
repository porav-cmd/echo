from typing import List, TypedDict
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from .rag_service import query_rag
from langchain_core.prompts import ChatPromptTemplate


class RagState(TypedDict):
    question: str
    user_id: int
    documents: List[str]
    sources: List[str]
    answer: str

def retrieve_node(state:RagState):
    question = state["question"]
    user_id = state["user_id"]
    retrieve_docs = query_rag(question,user_id = user_id)
    docs = [d.page_content for d in retrieve_docs]
    source = list(set([d.metadata.get("source","unknown")for d in retrieve_docs])) 
    return{"documents":docs,"sources":source}

def generate_code_node(state:RagState):
    document = "\n\n".join(state["documents"])
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a helpful AI assistant.
            Use ONLY the retrieved documents to answer the user's question.

            Instructions:
             - Base your answer entirely on the provided context.
             - Do not use outside knowledge.
             - If the answer cannot be found in the context, say "I don't know based on the provided documents."
              - Be clear, concise, and accurate.
            """
        ),("human", """Question:{question}Retrieved Documents:{documents}"""),
    ]
)

    chain = prompt | llm

    response = chain.invoke({"question": state["question"],"documents": "\n\n".join(state["documents"]),})
    return {"answer": response.content}

def fallback_node(state:RagState):
    return{"answer":"No relevant document found for your query","sources":[]}


def decide_to_generate(state: RagState) -> str:
    """Decides whether to route to generate node or fallback node."""
    if state.get("documents") and len(state["documents"]) > 0:
        return "generate"
    return "fallback"

workflow = StateGraph(RagState)

workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate_code_node)
workflow.add_node("fallback", fallback_node)


workflow.set_entry_point("retrieve")
workflow.add_conditional_edges("retrieve",decide_to_generate,{"generate": "generate","fallback": "fallback"})


workflow.add_edge("generate", END)
workflow.add_edge("fallback", END)

app_graph = workflow.compile()        

def run_langgraph_rag(question, user_id=1):
    initial_state = {
        "question": question,
        "user_id": user_id,
        "documents": [],
        "sources": [],
        "answer": ""
    }
    final_state = app_graph.invoke(initial_state)
    return {
        "question": final_state["question"],
        "answer": final_state["answer"],
        "sources": final_state.get("sources", []),
        "user_id": final_state["user_id"]
    }