# autograder/admin.py

from django.contrib import admin
from .models import Question, StudentAnswer

# Customize Question admin display
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_number', 'question_text', 'created_by', 'created_at')
    list_filter = ('question_number', 'created_by', 'created_at')
    search_fields = ('question_text', 'model_answer', 'keywords')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Question Info', {
            'fields': ('question_number', 'question_text', 'question_image')
        }),
        ('Model Answer & Keywords', {
            'fields': ('model_answer', 'keywords')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at')
        }),
    )

# Customize StudentAnswer admin display
@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'roll_number', 'question', 'score', 'submitted_at')
    list_filter = ('question', 'submitted_at', 'score')
    search_fields = ('student_name', 'roll_number', 'extracted_text')
    readonly_fields = ('submitted_at', 'extracted_text', 'score', 'matched_keywords', 'missing_keywords')
    
    fieldsets = (
        ('Student Info', {
            'fields': ('student_name', 'roll_number', 'question')
        }),
        ('Answer Details', {
            'fields': ('answer_image', 'extracted_text')
        }),
        ('Grading Results', {
            'fields': ('score', 'matched_keywords', 'missing_keywords')
        }),
        ('Metadata', {
            'fields': ('submitted_at',)
        }),
    )