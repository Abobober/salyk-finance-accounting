from django.db import models

class ChatSession(models.Model):
    session_id = models.CharField(max_length=255, unique=True)
    history = models.JSONField(default=list)  # [{"role": "user", "content": "..."}, ...]
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def append_message(self, role, content):
        self.history.append({"role": role, "content": content})
        self.save()
