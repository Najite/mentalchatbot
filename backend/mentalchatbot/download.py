import os
import requests
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from requests.exceptions import RequestException, Timeout


# setup logging for error monitoring and tracking
logger = logging.getLogger(__name__)

class ChatbotApiView(APIView):
    def post(self, request):
        user_input = request.data["user_input"]
        if not user_input:
            return Response({
                "error": "User input is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        url = "https://api.fireworks.ai/inference/v1/chat/completions"
        headers = {
            "Authorization": f"{os.getenv('FIREWORKS_API_KEY')}",
            "Content-Type": "application/json"
        }

        payload = {
            "messages": [{
                "role": "user",
                "content": user_input,
            }],
            "max_tokens": 150
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            response_data = response.json()

            ai_response = response.data["choices", [{}]][0]["message", {}]["content", "no valid response"]
            return Response(
                {"response": ai_response},
                status=status.HTTP_200_OK
                )
        
        except Timeout:
            logger.error("API request timed out")
            return Response({
                "error": "Request timed out. Please try again later"
            }, status=status.HTTP_504_GATEWAY_TIMEOUT)
        
        except RequestException as e:
            logger.error(f"Request exception: {e}")
            return Response({
                "error": "Failed to contact the server"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return Response({
                "error": "An unexpected error occured"
            })