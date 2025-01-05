# chatbot/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import MentalChatbotView
router = DefaultRouter()
router.register(r'chat', MentalChatbotView, basename='chatbot')
 
urlpatterns = [ 
        path('chat/<str:pk>/', MentalChatbotView.as_view({'get': 'retrieve'}), name='chatbot-detail'),  # Get conversation history

        path('', include(router.urls)),  # Handles chat interactions (session creation)
]