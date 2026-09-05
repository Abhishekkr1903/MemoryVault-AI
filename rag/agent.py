"""
MemoryVault Agent

Gemini decides whether to use a tool.
Python executes the requested tool.
The tool result is then sent back to Gemini
so Gemini can produce the final answer.
"""

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from rag.tools import (
    search_memory,
    list_memories,
    get_document_info,
    calculate,
)


load_dotenv()


# ==================================================
# CONFIGURATION
# ==================================================

MODEL_NAME = "gemini-3.5-flash"

# Maximum number of tool rounds.
# Keeps Gemini API usage under control.
MAX_TOOL_ROUNDS = 2


# ==================================================
# GEMINI CLIENT
# ==================================================

def get_client():

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY is missing."
        )

    return genai.Client(
        api_key=api_key
    )


# ==================================================
# TOOL FUNCTIONS
# ==================================================

def search_memory_tool(query: str):

    return search_memory(query)


def list_memories_tool():

    return list_memories()


def get_document_info_tool(
    document_id: int,
):

    return get_document_info(
        document_id
    )


def calculate_tool(
    expression: str,
):

    return calculate(
        expression
    )


# ==================================================
# TOOL DEFINITIONS
# ==================================================

search_memory_declaration = types.FunctionDeclaration(
    name="search_memory",
    description=(
        "Search the user's uploaded memories "
        "when the question requires personal "
        "or document information."
    ),
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "query": types.Schema(
                type="STRING",
                description=(
                    "The search query to use "
                    "against the user's memories."
                ),
            ),
        },
        required=["query"],
    ),
)


list_memories_declaration = types.FunctionDeclaration(
    name="list_memories",
    description=(
        "List all documents currently uploaded "
        "to MemoryVault."
    ),
)


get_document_info_declaration = types.FunctionDeclaration(
    name="get_document_info",
    description=(
        "Get metadata and information about "
        "a specific MemoryVault document."
    ),
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "document_id": types.Schema(
                type="INTEGER",
                description="The ID of the document.",
            ),
        },
        required=["document_id"],
    ),
)


calculate_declaration = types.FunctionDeclaration(
    name="calculate",
    description=(
        "Perform mathematical calculations."
    ),
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "expression": types.Schema(
                type="STRING",
                description=(
                    "A mathematical expression, "
                    "for example 25 * 42."
                ),
            ),
        },
        required=["expression"],
    ),
)


# ==================================================
# TOOL COLLECTION
# ==================================================

tools = types.Tool(
    function_declarations=[
        search_memory_declaration,
        list_memories_declaration,
        get_document_info_declaration,
        calculate_declaration,
    ]
)


# ==================================================
# EXECUTE TOOL
# ==================================================

def execute_tool(
    function_name,
    arguments,
):
    """
    Execute the Python function requested by Gemini.
    """

    print()
    print("==============================")
    print("TOOL EXECUTION")
    print("==============================")
    print("Tool:", function_name)
    print("Arguments:", arguments)
    print("==============================")

    if function_name == "search_memory":

        return search_memory_tool(
            arguments.get("query", "")
        )

    elif function_name == "list_memories":

        return list_memories_tool()

    elif function_name == "get_document_info":

        return get_document_info_tool(
            arguments.get("document_id")
        )

    elif function_name == "calculate":

        return calculate_tool(
            arguments.get("expression", "")
        )

    else:

        return {
            "success": False,
            "message": (
                f"Unknown tool: {function_name}"
            ),
        }


# ==================================================
# RUN AGENT
# ==================================================

def run_agent(
    question: str,
    chat_history: list[dict] | None = None,
):
    """
    Run the MemoryVault Agent.

    Flow:

        Question
            ↓
        Gemini
            ↓
        Tool call
            ↓
        Python tool
            ↓
        Tool result
            ↓
        Gemini
            ↓
        Final answer
    """

    client = get_client()

    if chat_history is None:
        chat_history = []

    # ----------------------------------------------
    # Build conversation context
    # ----------------------------------------------

    conversation_parts = []

    for item in chat_history:

        conversation_parts.append(
            f"User: {item.get('question', '')}"
        )

        conversation_parts.append(
            f"Assistant: {item.get('answer', '')}"
        )

    conversation_context = "\n".join(
        conversation_parts
    )

    # ----------------------------------------------
    # Agent prompt
    # ----------------------------------------------

    agent_prompt = f"""
You are MemoryVault AI, a personal AI assistant.

You have access to tools for:

- searching uploaded memories
- listing uploaded memories
- getting document information
- performing calculations

Use conversation history to understand follow-up questions.

For example:

Previous conversation:
User: Where did I intern?
Assistant: You interned at TechnoHacks EduTech.

Current question:
What did I do there?

Here, "there" refers to TechnoHacks EduTech.

Rules:

1. Use tools when information from the user's memories is required.

2. Use conversation history to resolve references such as:
   "there", "that company", "that project",
   "it", "this document", etc.

3. Do not invent personal information.

4. For calculations, use the calculate tool.

5. For uploaded-memory questions, use search_memory
   or another appropriate memory tool.

6. For questions asking what memories/documents exist,
   use list_memories.

7. For questions about a specific document,
   use get_document_info when appropriate.

8. For a memory question, normally call search_memory
   only once.

9. Do not repeatedly search the same question unless
   the previous search returned no useful information.

10. Once you have enough information, STOP using tools
    and provide the final answer.

11. Never invent information that was not provided by
    the user, conversation history, or tool results.

Conversation history:
{conversation_context}

Current question:
{question}
"""

    # ----------------------------------------------
    # First Gemini call
    # ----------------------------------------------

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=agent_prompt,
        config=types.GenerateContentConfig(
            tools=[tools],
        ),
    )

    # ----------------------------------------------
    # Tool loop
    # ----------------------------------------------

    for round_number in range(MAX_TOOL_ROUNDS):

        function_calls = response.function_calls

        # Gemini has produced the final answer.
        if not function_calls:

            if response.text:
                return response.text

            return (
                "I could not generate an answer."
            )

        print()
        print("==============================")
        print("AGENT TOOL ROUND")
        print("==============================")
        print(
            "Round:",
            round_number + 1,
            "/",
            MAX_TOOL_ROUNDS,
        )
        print("==============================")

        # ------------------------------------------
        # Execute requested tools
        # ------------------------------------------

        tool_results = []

        for function_call in function_calls:

            function_name = function_call.name
            arguments = function_call.args or {}

            result = execute_tool(
                function_name,
                arguments,
            )

            tool_results.append(
                types.Part.from_function_response(
                    name=function_name,
                    response=result,
                )
            )

        # ------------------------------------------
        # Send tool results back to Gemini
        # ------------------------------------------

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                agent_prompt,

                response.candidates[0].content,

                types.Content(
                    role="user",
                    parts=tool_results,
                ),
            ],
            config=types.GenerateContentConfig(
                tools=[tools],
            ),
        )

    # ----------------------------------------------
    # Tool limit reached
    # ----------------------------------------------

    if response.text:

        return response.text

    return (
        "I could not generate an answer from "
        "the available memories."
    )


# ==================================================
# DEBUG TEST
# ==================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("MEMORYVAULT AGENT TEST")
    print("=" * 60)

    questions = [
        "What is 2 + 2?",
        "What memories have I uploaded?",
        "Where did I intern?",
        "What technologies did I use to build MemoryVault?",
        "Show my Machine Learning projects.",
    ]

    for question in questions:

        print()
        print("=" * 60)
        print("QUESTION")
        print("=" * 60)

        print(question)

        try:

            answer = run_agent(
                question
            )

            print()
            print("=" * 60)
            print("FINAL ANSWER")
            print("=" * 60)

            print(answer)

        except Exception as error:

            print()
            print("=" * 60)
            print("ERROR")
            print("=" * 60)

            print(type(error).__name__)
            print(error)

    print()
    print("=" * 60)