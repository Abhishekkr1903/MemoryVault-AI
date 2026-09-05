"""
MemoryVault Agent Graph

LangGraph manages the loop:

    User
      ↓
    Agent
      ↓
  Tool needed?
    ↓     ↓
   YES    NO
    ↓      ↓
  Tools   END
    ↓
  Agent
    ↓
   ...
"""

from typing import TypedDict

from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from google import genai
from google.genai import types

import os

from dotenv import load_dotenv

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

# ==================================================
# AGENT CONFIGURATION
# ==================================================

MAX_TOOL_CALLS = 2

# ==================================================
# GRAPH STATE
# ==================================================
# ==================================================
# AGENT STATE
# ==================================================

class AgentState(TypedDict):

    question: str

    messages: list

    chat_history: list

    answer: str

    search_scope: str

    current_document_id: int | None

    selected_document_ids: list[int]

    retrieved_chunks: list

    tool_call_count: int

    tools_used: list[str]
# ==================================================
# GEMINI CLIENT
# ==================================================

def get_client():

    api_key = os.getenv(
        "GOOGLE_API_KEY"
    )

    if not api_key:

        raise ValueError(
            "GOOGLE_API_KEY is missing."
        )

    return genai.Client(
        api_key=api_key
    )


# ==================================================
# TOOL DEFINITIONS
# ==================================================

search_memory_declaration = (
    types.FunctionDeclaration(
        name="search_memory",
        description=(
            "Search the user's uploaded "
            "memories when the question "
            "requires personal or document "
            "information."
        ),
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "query": types.Schema(
                    type="STRING",
                    description=(
                        "The search query to "
                        "use against the "
                        "user's memories."
                    ),
                ),
            },
            required=["query"],
        ),
    )
)


list_memories_declaration = (
    types.FunctionDeclaration(
        name="list_memories",
        description=(
            "List all documents currently "
            "uploaded to MemoryVault."
        ),
    )
)


get_document_info_declaration = (
    types.FunctionDeclaration(
        name="get_document_info",
        description=(
            "Get metadata and information "
            "about a specific MemoryVault "
            "document."
        ),
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "document_id": types.Schema(
                    type="INTEGER",
                    description=(
                        "The ID of the document."
                    ),
                ),
            },
            required=["document_id"],
        ),
    )
)


calculate_declaration = (
    types.FunctionDeclaration(
        name="calculate",
        description=(
            "Perform mathematical "
            "calculations."
        ),
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "expression": types.Schema(
                    type="STRING",
                    description=(
                        "A mathematical "
                        "expression such as "
                        "25 * 42."
                    ),
                ),
            },
            required=["expression"],
        ),
    )
)


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
    state,
):

    print()
    print("==============================")
    print("LANGGRAPH TOOL NODE")
    print("==============================")
    print(
        "Tool:",
        function_name,
    )
    print(
        "Arguments:",
        arguments,
    )
    print("==============================")


    if function_name == "search_memory":

        return search_memory(
            query=arguments.get(
                "query",
                "",
            ),
            search_scope=state[
                "search_scope"
            ],
            current_document_id=state[
                "current_document_id"
            ],
            selected_document_ids=state[
                "selected_document_ids"
            ],
        )


    elif function_name == "list_memories":

        return list_memories()


    elif function_name == "get_document_info":

        return get_document_info(
            arguments.get(
                "document_id"
            )
        )


    elif function_name == "calculate":

        return calculate(
            arguments.get(
                "expression",
                "",
            )
        )


    return {
        "success": False,
        "message": (
            f"Unknown tool: "
            f"{function_name}"
        ),
    }


# ==================================================
# NODE 1 — AGENT
# ==================================================

def agent_node(
    state: AgentState,
):

    print()
    print("==============================")
    print("LANGGRAPH AGENT NODE")
    print("==============================")
    print(
        "Question:",
        state["question"],
    )
    print("==============================")


    client = get_client()


    # ==================================================
    # BUILD CONVERSATION HISTORY
    # ==================================================

    chat_history = state.get(
        "chat_history",
        [],
    )

    history_parts = []

    for item in chat_history:

        question = item.get(
            "question",
            "",
        )

        answer = item.get(
            "answer",
            "",
        )

        if question:

            history_parts.append(
                f"User: {question}"
            )

        if answer:

            history_parts.append(
                f"Assistant: {answer}"
            )


    history_text = "\n".join(
        history_parts
    )


    # ==================================================
    # AGENT INSTRUCTIONS
    # ==================================================

    agent_instructions = f"""
You are MemoryVault AI, a personal AI assistant.

You have access to these tools:

1. search_memory
   - Search information from the user's uploaded memories.

2. list_memories
   - List documents uploaded to MemoryVault.

3. get_document_info
   - Get information about a specific uploaded document.

4. calculate
   - Perform mathematical calculations.

IMPORTANT RULES:

- Use conversation history to understand follow-up questions.
- Resolve references such as:
  "there",
  "it",
  "that company",
  "that project",
  "this document",
  "the first one",
  "the second one".

- Use search_memory when information from uploaded memories is required.
- For a memory question, normally call search_memory only once.
- Do not repeatedly search the same question.
- Use list_memories when the user asks what documents/memories they have uploaded.
- Use get_document_info when information about a specific document is required.
- Use calculate for mathematical calculations.
- Do not invent personal information.
- If the user asks a general conversational question, answer normally.
- Once you have enough information, STOP using tools and provide the final answer.

SEARCH SCOPE:
{state["search_scope"]}

CURRENT DOCUMENT ID:
{state["current_document_id"]}

SELECTED DOCUMENT IDs:
{state["selected_document_ids"]}


CONVERSATION HISTORY:
{history_text}


CURRENT QUESTION:
{state["question"]}
"""


    # ==================================================
    # FIRST CALL / CONTINUE AFTER TOOL
    # ==================================================

    messages = state["messages"]


    # --------------------------------------------------
    # First Agent call
    # --------------------------------------------------

    if len(messages) == 1:

        messages_for_gemini = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(
                        text=agent_instructions
                    )
                ],
            )
        ]

    else:

        messages_for_gemini = messages


    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=messages_for_gemini,
        config=types.GenerateContentConfig(
            tools=[tools],
        ),
    )


    # ==================================================
    # TOOL REQUEST
    # ==================================================

    if response.function_calls:

        return {
            "messages": (
                state["messages"]
                + [
                    response.candidates[0].content
                ]
            )
        }


    # ==================================================
    # FINAL ANSWER
    # ==================================================

    return {

        "answer": response.text,

        "messages": (
            state["messages"]
            + [
                response.candidates[0].content
            ]
        ),

    }


# ==================================================
# NODE 2 — TOOLS
# ==================================================
def tool_node(
    state: AgentState,
):

    tool_call_count = state.get(
        "tool_call_count",
        0,
    )

    tools_used = state.get(
        "tools_used",
        [],
    )

    # -----------------------------------------------
    # Prevent excessive tool calls
    # -----------------------------------------------

    if tool_call_count >= MAX_TOOL_CALLS:

        print()
        print("==============================")
        print("TOOL LIMIT REACHED")
        print("==============================")
        print(
            "Tool calls:",
            tool_call_count,
        )
        print("==============================")

        return {
            "tool_call_count": tool_call_count,
            "tools_used": tools_used,
        }

    # -----------------------------------------------
    # Get the last Gemini response
    # -----------------------------------------------

    last_message = state["messages"][-1]

    # -----------------------------------------------
    # Preserve previous retrieved chunks
    # -----------------------------------------------

    retrieved_chunks = state.get(
        "retrieved_chunks",
        [],
    )

    tool_results = []

    # -----------------------------------------------
    # Execute requested tools
    # -----------------------------------------------

    for part in last_message.parts:

        if part.function_call is None:
            continue

        function_call = part.function_call

        function_name = function_call.name

        arguments = function_call.args or {}

        # -------------------------------------------
        # Check tool limit
        # -------------------------------------------

        if tool_call_count >= MAX_TOOL_CALLS:

            print()
            print("==============================")
            print("TOOL LIMIT REACHED")
            print("==============================")

            break

        # -------------------------------------------
        # Execute tool
        # -------------------------------------------

        result = execute_tool(
            function_name,
            arguments,
            state,
        )

        tool_call_count += 1

        tools_used.append(
            function_name
        )

        # -------------------------------------------
        # Preserve search results
        # -------------------------------------------

        if (
            function_name == "search_memory"
            and isinstance(result, dict)
        ):

            retrieved_chunks = result.get(
                "results",
                [],
            )

        # -------------------------------------------
        # Convert tool result to Gemini message
        # -------------------------------------------

        tool_results.append(
            types.Part.from_function_response(
                name=function_name,
                response=result,
            )
        )

    # -----------------------------------------------
    # Add tool result to graph state
    # -----------------------------------------------

    tool_message = types.Content(
        role="user",
        parts=tool_results,
    )

    return {

        "messages": (
            state["messages"]
            + [tool_message]
        ),

        "retrieved_chunks": (
            retrieved_chunks
        ),

        "tool_call_count": (
            tool_call_count
        ),

        "tools_used": (
            tools_used
        ),
    }
# ==================================================
# ROUTER — AGENT → TOOL OR END
# ==================================================
def tool_node(
    state: AgentState,
):

    tool_call_count = state.get(
        "tool_call_count",
        0,
    )

    tools_used = state.get(
        "tools_used",
        [],
    )

    retrieved_chunks = state.get(
        "retrieved_chunks",
        [],
    )

    last_message = state["messages"][-1]

    tool_results = []

    # ==================================================
    # EXECUTE REQUESTED TOOLS
    # ==================================================

    for part in last_message.parts:

        if part.function_call is None:
            continue

        function_call = part.function_call

        function_name = function_call.name

        arguments = (
            function_call.args
            or {}
        )

        # ----------------------------------------------
        # TOOL LIMIT
        # ----------------------------------------------

        if tool_call_count >= MAX_TOOL_CALLS:

            print()
            print("==============================")
            print("TOOL LIMIT REACHED")
            print("==============================")
            print(
                "Tool calls:",
                tool_call_count,
            )
            print(
                "Skipped tool:",
                function_name,
            )
            print("==============================")

            # IMPORTANT:
            # Send a valid function response back
            # to Gemini instead of returning nothing.

            tool_results.append(
                types.Part.from_function_response(
                    name=function_name,
                    response={
                        "success": False,
                        "message": (
                            "Tool call limit reached. "
                            "Do not call another tool. "
                            "Use the information already "
                            "retrieved and provide the "
                            "final answer."
                        ),
                    },
                )
            )

            continue

        # ----------------------------------------------
        # EXECUTE TOOL
        # ----------------------------------------------

        result = execute_tool(
            function_name,
            arguments,
            state,
        )

        tool_call_count += 1

        tools_used.append(
            function_name
        )

        # ----------------------------------------------
        # PRESERVE SEARCH RESULTS
        # ----------------------------------------------

        if (
            function_name == "search_memory"
            and isinstance(result, dict)
        ):

            retrieved_chunks = result.get(
                "results",
                [],
            )

        # ----------------------------------------------
        # CREATE FUNCTION RESPONSE
        # ----------------------------------------------

        tool_results.append(
            types.Part.from_function_response(
                name=function_name,
                response=result,
            )
        )

    # ==================================================
    # SAFETY
    # ==================================================

    if not tool_results:

        print(
            "WARNING: No tool results generated."
        )

        return {
            "messages": state["messages"],
            "retrieved_chunks": retrieved_chunks,
            "tool_call_count": tool_call_count,
            "tools_used": tools_used,
        }

    # ==================================================
    # SEND TOOL RESULTS BACK TO GEMINI
    # ==================================================

    tool_message = types.Content(
        role="user",
        parts=tool_results,
    )

    return {
        "messages": (
            state["messages"]
            + [tool_message]
        ),

        "retrieved_chunks": (
            retrieved_chunks
        ),

        "tool_call_count": (
            tool_call_count
        ),

        "tools_used": (
            tools_used
        ),
    }

def route_agent(
    state: AgentState,
):

    last_message = (
        state["messages"][-1]
    )


    # ------------------------------------------------
    # If Gemini requested a function
    # ------------------------------------------------

    for part in last_message.parts:

        if part.function_call is not None:

            return "tools"


    # ------------------------------------------------
    # Otherwise we have a final answer
    # ------------------------------------------------

    return "end"


# ==================================================
# BUILD GRAPH
# ==================================================

builder = StateGraph(
    AgentState
)


# ==================================================
# ADD NODES
# ==================================================

builder.add_node(
    "agent",
    agent_node,
)

builder.add_node(
    "tools",
    tool_node,
)


# ==================================================
# START → AGENT
# ==================================================

builder.add_edge(
    START,
    "agent",
)


# ==================================================
# AGENT → TOOL OR END
# ==================================================

builder.add_conditional_edges(
    "agent",
    route_agent,
    {
        "tools": "tools",
        "end": END,
    },
)


# ==================================================
# TOOL → AGENT
# ==================================================

builder.add_edge(
    "tools",
    "agent",
)


# ==================================================
# COMPILE
# ==================================================

memory_graph = builder.compile()