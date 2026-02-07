from django.urls import path
from . import views
from .views import grade_answer

urlpatterns = [
    path('grade/', views.grade_answer, name='grade_answer'),
    path('grade_answer/', grade_answer, name='grade_answer'),
   
]