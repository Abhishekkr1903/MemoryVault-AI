from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY")
)


def rewrite_question(question, chat_history):
    """
    Rewrite the user's question using previous conversation.

    Returns a standalone question that can be used for retrieval.
    """

    history = ""

    for chat in chat_history[-3:]:
        history += f"""
User: {chat['question']}
Assistant: {chat['answer']}
"""

    prompt = f"""
You are an AI assistant.

Your task is to rewrite the user's latest question
into a standalone search query.

The rewritten query should:

- include important context from previous conversation
- resolve pronouns like "it", "that", "this"
- include project names if mentioned
- include document context if relevant

Return ONLY the rewritten query.

Conversation History:

{history}

Current Question:
{question}

Return ONLY the rewritten question.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
    )

    return response.text.strip()