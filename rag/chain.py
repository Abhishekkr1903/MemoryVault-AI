"""
Generate answers using Gemini and retrieved memory context.
"""

from rag.model import generate


def generate_answer(question, retrieved_chunks):
    """
    Generate an answer using Gemini and retrieved memory chunks.

    Each retrieved result may contain:
    - filename
    - category
    - summary
    - keywords
    - language
    - chunk
    """

    context_parts = []

    for result in retrieved_chunks:

        filename = result.get(
            "filename",
            "Unknown document",
        )

        category = result.get(
            "category",
            "general",
        )

        summary = result.get(
            "summary",
            "",
        )

        keywords = result.get(
            "keywords",
            [],
        )

        language = result.get(
            "language",
            "Unknown",
        )

        chunk = result.get(
            "chunk",
            "",
        )

        context_parts.append(
            f"""
            Document: {filename}
            Category: {category}
            Language: {language}
            Summary: {summary}
            Keywords: {keywords}

            Content:{chunk}
            """
        )

    context = "\n\n".join(context_parts)

    prompt = f"""
        You are MemoryVault AI, a helpful personal knowledge assistant.

        Answer the user's question using ONLY the provided memory context.

        Rules:

        1. Use both document metadata and document content.
        2. Do not make up or assume information.
        3. If the requested information cannot be found
        in the provided memories, reply:

        "I could not find that information in the uploaded memories."

        4. If the user asks about a category, topic, or type
        of memory, use the metadata to identify relevant memories.
        5. Keep the answer clear and concise.
        6. Do not mention retrieval, embeddings, FAISS,
        BM25, RRF, or internal system details unless
        the user explicitly asks about them.

        Memory Context:
        {context}

        User Question:
        {question}

        Answer:
        """

    return generate(prompt)

# ==================================================
# GENERAL CHAT ANSWER
# ==================================================

def generate_chat_answer(question: str,chat_history: list) -> str:
    """
    Generate a normal conversational answer.

    This function does NOT use retrieved memories.
    It is used for greetings, calculations,
    general questions, etc.
    """

    history_text = ""

    if chat_history:

        history_lines = []

        for item in chat_history:

            history_lines.append(
                f"User: {item.get('question', '')}"
            )

            history_lines.append(
                f"Assistant: {item.get('answer', '')}"
            )

        history_text = "\n".join(
            history_lines
        )

    prompt = f"""
        You are MemoryVault AI, a helpful personal AI assistant.

        Answer the user's question naturally and directly.

        This is a normal conversation, not a memory retrieval request.

        Do NOT say that you could not find information in the user's memories.

        If the user asks a simple question such as:
        - hi
        - hello
        - how are you
        - what is 2+2

        answer it normally.

        Conversation history:
        {history_text}

        User question:
        {question}

        Answer:
        """

    return generate(prompt)