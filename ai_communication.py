# ai_communication.py
import requests

API_URL = "http://localhost:8080/completion"  # Llama API endpoint

def send_ai_request(prompt, max_tokens=100):
    """Sends a request to the AI and returns the response."""
    try:
        response = requests.post(API_URL, json={"prompt": prompt, "max_tokens": max_tokens})
        if response.status_code == 200:
            full_response = response.json().get("content", "No response received from AI.")
            return split_message(full_response, 250)  # Split into chunks of 250 characters
        else:
            return [f"AI request failed with status code {response.status_code}"]
    except Exception as e:
        return [f"Error communicating with AI: {e}"]

def split_message(message, max_length):
    """Splits a message into chunks of max_length characters."""
    return [message[i:i+max_length] for i in range(0, len(message), max_length)]
