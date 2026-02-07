# Create your models here.
from django.db import models

class StudentAnswer(models.Model):
    student_name = models.CharField(max_length=100)
    uploaded_image = models.ImageField(upload_to='')  # image ma gayera store huncha
    extracted_text = models.TextField(blank=True)
    marks = models.FloatField(default=0.0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.student_name
