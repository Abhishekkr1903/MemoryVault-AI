import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

MODEL_NAME = "gemini-3.5-flash"


def get_llm():
    """
    Return a configured Gemini client.
    """

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY is missing. Please add it to your .env file."
        )

    return genai.Client(api_key=api_key)


def generate(prompt):
    """
    Generate text using Gemini.
    """

    client = get_llm()

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )

    return response.text

def generate_stream(prompt):
    """
    Stream Gemini's final text response.
    """

    client = get_llm()

    response = client.models.generate_content_stream(
        model=MODEL_NAME,
        contents=prompt,
    )

    for chunk in response:

        if chunk.text:
            yield chunk.text