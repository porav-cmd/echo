import os
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import ChatHistory, DocumentsMetaData
from .rag_service import load_document, generate_rag_answer
from .langgraph_service import run_langgraph_rag
from .supervisor_service import route_and_execute


# ==========================================
# FULL-STACK DJANGO WEB DASHBOARD VIEWS
# ==========================================

def home_view(request):
    """
    Main Full-Stack Web Interface view handling Chat form submissions, 
    File Upload Ingestions, tab switching, and dynamic database context rendering.
    """
    active_tab = request.GET.get("tab", "chat")
    is_new_chat = request.GET.get("new") == "1"
    user_id = request.user.id if request.user.is_authenticated else 1

    if request.method == "POST":
        action_type = request.POST.get("action_type")

        # Handle Chat Questions
        if action_type == "chat":
            active_tab = "chat"
            query = request.POST.get("query", "").strip()

            if query:
                result = route_and_execute(query, user_id=user_id)
                owner_user = request.user if request.user.is_authenticated else User.objects.first()

                ChatHistory.objects.create(
                    owner=owner_user,
                    query=query,
                    answer=result.get("answer", ""),
                    intent=result.get("intent", "RAG"),
                )

        # Handle File Upload Ingestion
        elif action_type == "ingest":
            active_tab = "documents"
            if "document" in request.FILES:
                uploaded_file = request.FILES["document"]
                
                os.makedirs("media/uploads", exist_ok=True)
                fs = FileSystemStorage(location="media/uploads")
                fs.save(uploaded_file.name, uploaded_file)

                result = load_document("media/uploads", user_id=user_id)
                owner_user = request.user if request.user.is_authenticated else User.objects.first()

                DocumentsMetaData.objects.create(
                    owner=owner_user,
                    filename=uploaded_file.name,
                    total_chunks=result.get("total_chunks", 0),
                )

    # Database Queries for Template Context
    if is_new_chat:
        chat_history = []
    else:
        if request.user.is_authenticated:
            chat_history = ChatHistory.objects.filter(owner=request.user).order_by("created_at")
        else:
            chat_history = ChatHistory.objects.all().order_by("created_at")

    if request.user.is_authenticated:
        documents = DocumentsMetaData.objects.filter(owner=request.user).order_by("-created_at")
    else:
        documents = DocumentsMetaData.objects.all().order_by("-created_at")

    return render(
        request,
        "index.html",
        {
            "chat_history": chat_history,
            "documents": documents,
            "active_tab": active_tab,
        },
    )


def login_view(request):
    """
    Session-based User Login Handler.
    """
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("/")
    return redirect("/?error=invalid_credentials")


def logout_view(request):
    """
    Session-based User Logout Handler.
    """
    logout(request)
    return redirect("/")


def web_register_view(request):
    """
    Session-based User Registration Handler.
    """
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if username and password:
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(username=username, email=email, password=password)
                login(request, user)
                return redirect("/")
    return redirect("/?error=registration_failed")


def new_chat_view(request):
    """
    Resets active conversation view without deleting historical database records.
    """
    return redirect("/?new=1")


# ==========================================
# REST API ENDPOINTS (JWT AUTHENTICATED)
# ==========================================

@api_view(['GET'])
def health_check(request):
    """
    GET /api/v1/health/ -> API Server Status Check.
    """
    return Response(
        {
            "status": "ok",
            "message": "Enterprise Knowledge Assistant API is online"
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ingest_documents_view(request):
    """
    POST /api/v1/ingest/ -> JWT Authenticated Document Ingestion Endpoint.
    """
    directory = request.data.get("directory", "data")
    user_id = request.user.id
    result = load_document(directory, user_id=user_id)
    
    DocumentsMetaData.objects.create(
        owner=request.user,
        filename=directory,
        total_chunks=result.get("total_chunks", 0)
    )

    if "error" in result:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    return Response(result, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def ask_question_view(request):
    """
    POST /api/v1/ask/ -> RAG Generation Endpoint.
    """
    query = request.data.get("query")
    user_id = request.data.get("user_id", 1)
    if not query:
        return Response({"error": "query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    result = generate_rag_answer(query, user_id=user_id)
    return Response(result, status=status.HTTP_200_OK)


@api_view(['POST'])
def graph_ask_view(request):
    """
    POST /api/v1/graph-ask/ -> LangGraph Stateful Agent Execution Endpoint.
    """
    query = request.data.get("query")
    user_id = request.data.get("user_id", 1)
    if not query:
        return Response({"error": "query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    result = run_langgraph_rag(query, user_id=user_id)
    return Response(result, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def supervisor_view(request):
    """
    POST /api/v1/supervisor/ -> Multi-Agent Supervisor Router Endpoint.
    """
    query = request.data.get("query")
    user_id = request.user.id
    if not query:
        return Response({"error": "query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    result = route_and_execute(query, user_id=user_id)
    ChatHistory.objects.create(
        owner=request.user,
        query=query,
        answer=result.get("answer", ""),
        intent=result.get("intent", "RAG")
    )
    return Response(result, status=status.HTTP_200_OK)


@api_view(['POST'])
def register_view(request):
    """
    POST /api/v1/register/ -> JWT User Registration Endpoint.
    """
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    if not username or not password:
        return Response({"error": "Username and password are required"}, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(username=username).exists():
        return Response({"error": "Username is already taken"}, status=status.HTTP_400_BAD_REQUEST)
    
    User.objects.create_user(username=username, email=email, password=password)
    return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_history_view(request):
    """
    GET /api/v1/history/ -> JWT Authenticated User History Retrieval.
    """
    records = ChatHistory.objects.filter(owner=request.user).order_by('-created_at')
    history_data = [
        {
            "query": r.query,
            "answer": r.answer,
            "intent": r.intent,
            "created_at": r.created_at
        }
        for r in records
    ]
    return Response({"history": history_data}, status=status.HTTP_200_OK)