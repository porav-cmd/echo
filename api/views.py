from django.shortcuts import render

from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from rest_framework import status
from .rag_service import*
from .langgraph_service import run_langgraph_rag 
from .supervisor_service import route_and_execute
from django.contrib.auth.models import User 
from rest_framework.permissions import IsAuthenticated 
from .models import *
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect





def home_view(request):
    active_tab = request.GET.get("tab", "chat")
    user_id = request.user.id if request.user.is_authenticated else 1

    if request.method == "POST":
        action_type = request.POST.get("action_type")

        
        if action_type == "chat":
            active_tab = "chat"
            query = request.POST.get("query", "").strip()
            if query:
                result = route_and_execute(query, user_id=user_id)
                ChatHistory.objects.create(
                    owner=request.user if request.user.is_authenticated else User.objects.first(),
                    query=query,
                    answer=result.get("answer", ""),
                    intent=result.get("intent", "RAG"),
                )

        
        elif action_type == "ingest":
            active_tab = "documents"
            if "document" in request.FILES:
                uploaded_file = request.FILES["document"]
                os.makedirs("media/uploads", exist_ok=True)
                fs = FileSystemStorage(location="media/uploads")
                fs.save(uploaded_file.name, uploaded_file)
                
                result = load_document("media/uploads", user_id=user_id)
                DocumentsMetaData.objects.create(
                    owner=request.user if request.user.is_authenticated else User.objects.first(),
                    filename=uploaded_file.name,
                    total_chunks=result.get("total_chunks", 0),
                )

    chat_history = ChatHistory.objects.all().order_by("created_at")
    documents = DocumentsMetaData.objects.all().order_by("-created_at")


    is_new_chat = request.GET.get('new') == '1'
    if is_new_chat:
     chat_history = []  # Start blank screen for new conversation!
    else:
     chat_history = ChatHistory.objects.all().order_by("created_at")
    return render(request,
    "index.html",
        {
            "chat_history": chat_history,
            "documents": documents,
            "active_tab": active_tab,
        },
    )



@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint to verify API server status.
    GET /api/v1/health/
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
    """ Ingest document from directory into te vector database"""
    directory = request.data.get("directory","data")
    user_id = request.user.id
    result = load_document(directory,user_id = user_id)
    DocumentsMetaData.objects.create(
    owner=request.user,
    filename=directory,
    total_chunks=result.get("total_chunks", 0)
    )
    if "error" in result:
        return Response(result,status=status.HTTP_400_BAD_REQUEST)

    return Response(result, status = status.HTTP_201_CREATED)  


@api_view(['POST'])
def ask_question_view(request):
    query = request.data.get("query")
    user_id= request.data.get("user_id",1)
    if not query:
        return Response({"error":"query is required"},status = status.HTTP_400_BAD_REQUEST)
    result = generate_rag_answer(query,user_id = user_id)    
    return Response(result, status= status.HTTP_200_OK)
    
@api_view(['POST'])
def graph_ask_view(request):
    query = request.data.get("query")
    user_id = request.data.get("user_id",1)
    if not query:
        return Response({"error":"query is required"},status = status.HTTP_400_BAD_REQUEST)
    result = run_langgraph_rag(query,user_id = user_id)    
    return Response(result, status= status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def supervisor_view(request):
    query = request.data.get("query")
    user_id = request.user.id
    if not query:
        return Response({"error":"Query is required"}, status = status.HTTP_400_BAD_REQUEST)
    result = route_and_execute(query,user_id=user_id)
    ChatHistory.objects.create(owner=request.user,query=query,answer=result.get("answer", ""),intent=result.get("intent", "RAG"))
    return Response(result,status=status.HTTP_200_OK)


@api_view(['POST'])
def register_view(request):
    if request.method =='POST':
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
    if not username or not email or not password:
        return Response({"error":"Username, email, and password are required"},status = status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(username=username).exists():
        return Response({"error":"username is already taken"}, status = status.HTTP_400_BAD_REQUEST)    
    user = User.objects.create_user(username = username, email = email, password = password)   
    return Response({"message":"User registered successfully"}, status= status.HTTP_201_CREATED)
    
   
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_history_view(request):
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

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
        
            return redirect('/?error=invalid_credentials')
    return redirect('/')

def logout_view(request):
    logout(request)
    return redirect('/')        

def web_register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if username and password:
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(username=username, email=email, password=password)
                login(request, user)  
                return redirect('/')
    return redirect('/?error=registration_failed') 

def new_chat_view(request):
    """
    Starts a fresh chat thread without deleting past history from the database!
    """
    return redirect('/?new=1')      