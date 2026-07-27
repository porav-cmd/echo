from django.urls import path
from .views import *

urlpatterns = [
    path("health/", health_check),
    path('ingest/', ingest_documents_view, name='ingest_documents'),
    path('ask/', ask_question_view, name='ask_question'),
    path('graph-ask/',graph_ask_view ,name = 'graph_ask'),
    path('supervisor/',supervisor_view,name = 'supervisor'),
    path('register/', register_view, name='register'),
    path('history/', user_history_view, name='user_history'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]

