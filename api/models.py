from django.db import models
from django.contrib.auth.models import User 

class DocumentsMetaData(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    filename = models.CharField(max_length=255)
    total_chunks = models.IntegerField(default = 0)
    created_at = models.DateTimeField(auto_now_add=True)

class ChatHistory(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.TextField()
    answer = models.TextField()
    intent = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
