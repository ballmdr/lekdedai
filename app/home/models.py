from django.db import models

class HomePage(models.Model):
    title = models.CharField(max_length=255, default="LekDedAI")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title