import os

from dotenv import load_dotenv


load_dotenv()


class Settings:

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


settings = Settings()

# fallback , if ollama model fails (this part need to be implemented in the future)