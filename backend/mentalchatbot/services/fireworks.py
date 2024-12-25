import logging
import requests


# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Fireworks API Service
class FireworksAPIService:
    def __init__(self):
        self.api_url = "https://api.fireworks.ai/inference/v1/chat/completions"
        self.api_key = "fw_3Zcc6Vj1rh2Fi2vQZFESjRbT"

        if not self.api_key:
            raise RuntimeError("Fireworks API key not found.")

    def get_completion(self, prompt):
        """
        Send a request to the Fireworks API to get a chatbot response based on the prompt.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "accounts/fireworks/models/llama-v3p1-8b-instruct",
            "messages": [
                {"role": "system", "content": "This is a mental health chatbot."},
                {"role": "user", "content": prompt},
            ],
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            raise RuntimeError("Fireworks API request failed.")
        except Exception as err:
            logger.error(f"Other error occurred: {err}")
            raise RuntimeError("An error occurred while communicating with the Fireworks API.")