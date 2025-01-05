from rest_framework import viewsets, status
from django.http import JsonResponse
from django.utils.timezone import now
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import logging
from .models import Conversation, Message
from services.fireworks import FireworksAPIService

logger = logging.getLogger(__name__)

# Load models at server initialization
MODELS = {}

def preload_models():
    global MODELS
    logger.info("Preloading models...")
    toxicity_model_name = "unitary/unbiased-toxic-roberta"
    mental_health_model_name = "SamLowe/roberta-base-go_emotions"
    
    # Load models and tokenizers
    MODELS["toxicity"] = {
        "tokenizer": AutoTokenizer.from_pretrained(toxicity_model_name),
        "model": AutoModelForSequenceClassification.from_pretrained(toxicity_model_name)
    }
    MODELS["mental_health"] = {
        "tokenizer": AutoTokenizer.from_pretrained(mental_health_model_name),
        "model": AutoModelForSequenceClassification.from_pretrained(mental_health_model_name)
    }

preload_models()

class MentalChatbotView(viewsets.ViewSet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fireworks_service = FireworksAPIService()

    def classify_text(self, tokenizer, model, text, labels):
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            logits = model(**inputs).logits
        predicted_class = torch.argmax(logits, dim=-1).item()
        return labels[predicted_class]

    def classify_toxicity(self, text):
        toxicity_data = MODELS["toxicity"]
        labels = toxicity_data["model"].config.id2label
        return self.classify_text(toxicity_data["tokenizer"], toxicity_data["model"], text, labels)

    def classify_mental_health(self, text):
        mental_health_data = MODELS["mental_health"]
        labels = mental_health_data["model"].config.id2label
        return self.classify_text(mental_health_data["tokenizer"], mental_health_data["model"], text, labels)

    def create(self, request, *args, **kwargs):
        user_input = request.data.get("input", "").strip()
        if not user_input:
            return JsonResponse({"error": "Input text is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not request.session.session_key:
            request.session.create()

        session_id = request.session.session_key
        conversation, created = Conversation.objects.get_or_create(session_id=session_id, defaults={'created_at': now()})

        # Classify text for toxicity and mental health
        toxicity_label = self.classify_toxicity(user_input)
        if toxicity_label.lower() == "toxic":
            return JsonResponse({"response": "Your input contains harmful or toxic content. Please modify your message.", "session_id": session_id}, status=status.HTTP_200_OK)

        mental_health_label = self.classify_mental_health(user_input)
        if mental_health_label.lower() == "neutral":
            return JsonResponse({"response": "I can only handle mental health-related conversations.", "session_id": session_id}, status=status.HTTP_200_OK)

        # Generate response using FireworksAPIService
        try:
            response_data = self.fireworks_service.get_completion(user_input)
            chatbot_response = response_data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

            # Save the input and response as a Message
            Message.objects.create(conversation=conversation, input=user_input, response=chatbot_response, timestamp=now())

            return JsonResponse({"session_id": session_id, "input": user_input, "response": chatbot_response, "toxicity_label": toxicity_label, "mental_health_label": mental_health_label}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error during response generation: {str(e)}")
            return JsonResponse({"error": "An error occurred while generating the response.", "session_id": session_id}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
