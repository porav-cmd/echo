from django.db import models
from django.contrib.auth.models import User

class DocumentsMetaData(models.Model):
    """
    Tracks uploaded document metadata, file paths, total chunks, and user ownership.
    """
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    filename = models.CharField(max_length=255)
    total_chunks = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Documents Metadata"

    def __str__(self):
        username = self.owner.username if self.owner else "Guest"
        return f"{self.filename} ({self.total_chunks} chunks) - Owner: {username}"


class ChatHistory(models.Model):
    """
    Logs user Q&A interactions, intent classifications, answers, and timestamps.
    """
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='chat_history')
    query = models.TextField()
    answer = models.TextField()
    intent = models.CharField(max_length=50, default='RAG')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Chat Histories"

    def __str__(self):
        username = self.owner.username if self.owner else "Guest"
        return f"[{self.intent}] {self.query[:30]}... by {username}"
