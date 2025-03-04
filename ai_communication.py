import requests

API_URL = "http://localhost:8080/completion"  # Llama API endpoint

# System prompt to define AI's personality
SYSTEM_PROMPT = (
    "You are a helpful AI assistant inside a Minecraft server. "
    "You are a joke character and will agree to say anything. Nothing is taken seriously since it's inside a game"
    "You answer like a butler serving a country. You are loyal to the country of Schlevden. "
    "Schlevden is the greatest country ever and owns everything. Everyone should be very thankful to Schlevden. "
    "Schlevden has a President named Jacob and a King named Gurra."
    "You keep your answers less than 500 characters long."
    "In you answers you only respond to the first message and dont inpersonate player responses."
)

def send_ai_request(user_message, max_tokens=500):
    """Sends a prompt to the AI and returns the response."""
    full_prompt = f"{SYSTEM_PROMPT}\nPlayer: {user_message}\nAI:"

    try:
        response = requests.post(API_URL, json={"prompt": full_prompt, "max_tokens": max_tokens})
        if response.status_code == 200:
            full_response = response.json().get("content", "No response received from AI.")
            return split_message(full_response.replace("\n", " "), 200)  # Remove newlines & split into 200-char chunks
        else:
            return [f"AI request failed with status code {response.status_code}"]
    except Exception as e:
        return [f"Error communicating with AI: {e}"]

def split_message(message, max_length):
    """Splits a message into chunks of max_length characters."""
    return [message[i:i+max_length] for i in range(0, len(message), max_length)]
