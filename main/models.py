from django.db import models

# Create your models here.

class Message(models.Model):
    title = models.CharField(max_length=200)
    email = models.EmailField()
    content = models.TextField()
    sent = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent']

    def __str__(self):
        return f"{self.title} | {self.email}"