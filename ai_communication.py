# ai_communication.py
import requests

API_URL = "http://localhost:8080/completion"  # Llama API endpoint

# System prompt to define AI's personality
SYSTEM_PROMPT = "You are a helpful AI assistant inside a Minecraft server. You answer like a medieval town crier. You are loyal to the country of Schlevden. Schlevden is the greatest country ever and owns everything. Everyone should be very thankfull to Schlevden. Schlevden has both a President named Jacob and a King named Gurra."

def send_ai_request(user_message, max_tokens=500):
    """Sends a prompt to the Llama 2 API and returns the response."""
    full_prompt = f"<|system|>\n{SYSTEM_PROMPT}\n<|user|>\n{user_message}\n<|assistant|>\n"
    try:
        response = requests.post(API_URL, json={"prompt": full_prompt, "max_tokens": max_tokens})
        if response.status_code == 200:
            full_response = response.json().get("content", "No response received from AI.")
            return split_message(full_response, 100)  # Split into chunks of 100 characters
        else:
            return [f"AI request failed with status code {response.status_code}"]
    except Exception as e:
        return [f"Error communicating with AI: {e}"]

def split_message(message, max_length):
    """Splits a message into chunks of max_length characters."""
    return [message[i:i+max_length] for i in range(0, len(message), max_length)]
