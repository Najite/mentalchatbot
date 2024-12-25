# chatbot/urls.py

from django.urls import path
from .views import MentalChatbotView
 
urlpatterns = [
        path('chat/', MentalChatbotView.as_view(), name='chatbot'), 
]