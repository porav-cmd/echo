from django.urls import path
from .views import (
    health_check,
    ingest_documents_view,
    ask_question_view,
    graph_ask_view,
    supervisor_view,
    register_view,
    user_history_view,
)

app_name = 'api'

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('ingest/', ingest_documents_view, name='ingest_documents'),
    path('ask/', ask_question_view, name='ask_question'),
    path('graph-ask/', graph_ask_view, name='graph_ask'),
    path('supervisor/', supervisor_view, name='supervisor'),
    path('register/', register_view, name='register'),
    path('history/', user_history_view, name='user_history'),
]
