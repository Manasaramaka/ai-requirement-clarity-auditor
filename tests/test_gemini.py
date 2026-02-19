import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# Load .env file explicitly
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# Read environment variables
api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Check your .env file.")

# Initialize Gemini client
client = genai.Client(api_key=api_key)

# Make a simple test call
response = client.models.generate_content(
    model=model_name,
    contents="Reply with exactly: Gemini is connected"
)

# Print result
print(response.text.strip())
