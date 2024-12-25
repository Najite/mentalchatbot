import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from services.fireworks import FireworksAPIService

# Configure logging for monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the tokenizer and model for toxicity classification
toxicity_tokenizer = AutoTokenizer.from_pretrained("unitary/unbiased-toxic-roberta")
toxicity_model = AutoModelForSequenceClassification.from_pretrained("unitary/unbiased-toxic-roberta")

# Load the tokenizer and model for mental health classification
mental_health_tokenizer = AutoTokenizer.from_pretrained("SamLowe/roberta-base-go_emotions")
mental_health_model = AutoModelForSequenceClassification.from_pretrained("SamLowe/roberta-base-go_emotions")

# View available labels for both models
toxicity_labels = toxicity_model.config.id2label
mental_health_labels = mental_health_model.config.id2label
logger.info(f"Toxicity Labels: {toxicity_labels}")
logger.info(f"Mental Health Labels: {mental_health_labels}")


class MentalChatbotView(APIView):
    """
    API view to classify the toxicity and mental health relevance of user input,
    and generate a response using the Fireworks API.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fireworks_service = FireworksAPIService()  # Initialize Fireworks API service

    def classify_text(self, tokenizer, model, text, labels):
        """
        Classify the input text using the given tokenizer and model.
        Returns the predicted label.
        """
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)

        with torch.no_grad():
            logits = model(**inputs).logits

        predicted_class = torch.argmax(logits, dim=-1).item()
        logger.info(f"Classification - Text: {text}, Prediction: {labels[predicted_class]}")
        return labels[predicted_class]

    def classify_toxicity(self, text):
        """
        Classify the toxicity of the input text.
        """
        return self.classify_text(toxicity_tokenizer, toxicity_model, text, toxicity_labels)

    def classify_mental_health(self, text):
        """
        Classify the mental health relevance of the input text.
        """
        return self.classify_text(mental_health_tokenizer, mental_health_model, text, mental_health_labels)

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests: processes user input, checks toxicity, checks mental health relevance,
        and calls the Fireworks API if valid.
        """
        user_input = request.data.get("input", "").strip()

        if not user_input:
            logger.warning("Received empty input.")
            return Response(
                {"error": "Input text is required and cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Step 1: Classify the toxicity of the input
        toxicity_label = self.classify_toxicity(user_input)
        if toxicity_label.lower() == "toxic":
            logger.warning("Detected toxic content in the input.")
            return Response(
                {"response": "Your input contains harmful or toxic content. Please modify your message."},
                status=status.HTTP_200_OK,
            )

        # Step 2: Classify mental health relevance
        mental_health_label = self.classify_mental_health(user_input)
        if mental_health_label.lower() == "neutral":
            logger.info("Input is not related to mental health.")
            return Response(
                {"response": "I can only handle mental health-related conversations. Please send another message."},
                status=status.HTTP_200_OK,
            )

        # Step 3: If input is valid, call Fireworks API for a response
        try:
            response_data = self.fireworks_service.get_completion(user_input)
            chatbot_response = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

            logger.info(f"Fireworks response: {chatbot_response}")
            return Response({
                "toxicity_label": toxicity_label,
                "mental_health_label": mental_health_label,
                "response": chatbot_response,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return Response(
                {"error": "An error occurred while generating the response. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ) 