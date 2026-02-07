# autograder/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('simple-test/', views.simple_test_page, name='simple_test'),
    
    # Teacher URLs
    path('teacher/login/', views.teacher_login, name='teacher_login'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/add-question/', views.add_question, name='add_question'),
    path('teacher/questions/', views.view_questions, name='view_questions'),
    
    # Student URLs
    path('student/upload/', views.student_upload, name='student_upload'),
    path('student/result/<int:answer_id>/', views.view_result, name='view_result'),
    
    # API endpoints
    path('grade/', views.simple_grade, name='simple_grade'),
]