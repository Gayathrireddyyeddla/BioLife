from django.db import models

class Click(models.Model):
    clicked_time = models.DateTimeField(auto_now_add=True)
    button_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.button_name} clicked at {self.clicked_time}"