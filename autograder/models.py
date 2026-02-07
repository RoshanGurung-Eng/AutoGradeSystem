# autograder/models.py - ADD THESE METHODS

from django.db import models
from django.contrib.auth.models import User

class Question(models.Model):
    question_number = models.CharField(max_length=10)
    question_text = models.TextField()
    question_image = models.ImageField(upload_to='questions/', blank=True, null=True)
    model_answer = models.TextField(blank=True)
    keywords = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_keywords_list(self):
        if not self.keywords:
            return []
        return [k.strip().lower() for k in self.keywords.split(',') if k.strip()]
    
    def __str__(self):
        return f"{self.question_number}: {self.question_text[:50]}"

class StudentAnswer(models.Model):
    student_name = models.CharField(max_length=200, blank=True, null=True)
    roll_number = models.CharField(max_length=50, blank=True, null=True)
    question = models.ForeignKey(Question, on_delete=models.SET_NULL, null=True, blank=True, related_name='answers')
    answer_image = models.ImageField(upload_to='student_answers/', blank=True, null=True)
    extracted_text = models.TextField(blank=True)
    score = models.FloatField(default=0.0)
    matched_keywords = models.TextField(blank=True)
    missing_keywords = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    def get_matched_list(self):
        if not self.matched_keywords:
            return []
        return [k.strip() for k in self.matched_keywords.split(',') if k.strip()]
    
    def get_missing_list(self):
        if not self.missing_keywords:
            return []
        return [k.strip() for k in self.missing_keywords.split(',') if k.strip()]
    
    def __str__(self):
        return f"{self.student_name} - {self.question.question_number if self.question else 'No Question'}"