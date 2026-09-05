import streamlit as st
import database.db as db

import re

from rag.graph import memory_graph

def generate_conversation_title(question: str) -> str:
    """
    Generate a short conversation title locally.

    No Gemini/API call is used.
    """

    question = " ".join(
        question.strip().split()
    )

    if not question:
        return "New Chat"

    # Remove common question starters
    title = re.sub(
        r"^(what|where|when|why|how|who|can|could|would|show|tell|give|list)\s+",
        "",
        question,
        flags=re.IGNORECASE,
    )

    title = title.strip(
        " ?.!,:;"
    )

    if not title:
        title = question

    # Keep the title short
    words = title.split()

    if len(words) > 7:
        title = " ".join(words[:7]) + "..."

    # Capitalize first character
    title = title[0].upper() + title[1:]

    return title[:60]

def render_chat_page():
    """Render chat page."""

    st.header("💬 Chat with MemoryVault AI")

    # ==================================================
    # Current Conversation
    # ==================================================

    conversation_id = st.session_state.get(
        "conversation_id"
    )

    if conversation_id is None:

        st.info(
            "Create a new conversation from the sidebar."
        )

        return

    # ==================================================
    # Load Messages
    # ==================================================

    messages = db.get_messages(
        conversation_id
    )

    # ==================================================
    # Ensure Memory Loaded
    # ==================================================

    if (
        "chunks" not in st.session_state
        or "index" not in st.session_state
    ):

        st.warning(
            "No memory is currently loaded. "
            "Please select one from 'Current Memory' "
            "in the sidebar."
        )

        return

    # ==================================================
    # Search Scope
    # ==================================================

    search_scope = st.session_state.get(
        "search_scope",
        "Current Memory",
    )

    selected_document_ids = st.session_state.get(
        "selected_document_ids",
        [],
    )

    current_document_id = st.session_state.get(
        "selected_document_id"
    )

    # ==================================================
    # Clear Chat
    # ==================================================

    col1, col2 = st.columns([8, 1])

    with col2:

        if st.button("🗑 Clear Chat"):

            db.clear_messages(
                conversation_id
            )

            st.rerun()

    st.divider()

    # ==================================================
    # Display Previous Messages
    # ==================================================

    chat_history = []

    for role, message, created_at in messages:

        with st.chat_message(role):

            st.markdown(message)

        if role == "user":

            chat_history.append(
                {
                    "question": message,
                    "answer": "",
                }
            )

        elif role == "assistant" and chat_history:

            chat_history[-1]["answer"] = message

    # ==================================================
    # Chat Input
    # ==================================================

    question = st.chat_input(
        "Ask anything about your memories..."
    )

    if not question:
        return

    # ==================================================
    # Save User Message
    # ==================================================

    db.save_message(
    conversation_id,
    "user",
    question,
    )


    # ==================================================
    # AUTO-NAME NEW CONVERSATION
    # ==================================================

    conversation = db.get_conversation(
        conversation_id
    )

    if (
        conversation
        and conversation[1] == "New Chat"
    ):

        conversation_title = (
            generate_conversation_title(
                question
            )
        )

        db.rename_conversation(
            conversation_id,
            conversation_title,
        )

    # ==================================================
    # Display User Message
    # ==================================================

    with st.chat_message("user"):

        st.markdown(question)

    # ==================================================
    # PREPARE DOCUMENT IDs FOR GRAPH
    # ==================================================

    if search_scope == "Current Memory":

        graph_document_ids = (
            [current_document_id]
            if current_document_id is not None
            else []
        )

    elif search_scope == "Selected Memories":

        if len(selected_document_ids) == 0:

            st.warning(
                "Please select one or more memories "
                "from the sidebar."
            )

            return

        graph_document_ids = selected_document_ids

    else:

        # All Memories
        #
        # The graph will decide which memories
        # are relevant using metadata filtering.

        graph_document_ids = []

    # ==================================================
    # PREPARE GRAPH STATE
    # ==================================================
    graph_state = {
        "question": question,

        "messages": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": question
                    }
                ]
            }
        ],

        "chat_history": chat_history,

        "search_scope": search_scope,
        "current_document_id": current_document_id,
        "selected_document_ids": graph_document_ids,

        "route": "",

        "rewritten_question": "",
        "document_ids": None,
        "retrieved_chunks": [],
        "answer": "",
    }
    # ==================================================
    # DEBUG
    # ==================================================

    print("\n==============================")
    print("CHAT PAGE DEBUG")
    print("==============================")

    print(
        "Search Scope:",
        search_scope
    )

    print(
        "Current Document ID:",
        current_document_id
    )

    print(
        "Selected Document IDs:",
        selected_document_ids
    )

    print(
        "Graph Document IDs:",
        graph_document_ids
    )

    print("==============================")

    # ==================================================
    # RUN LANGGRAPH
    # ==================================================

    with st.spinner(
        "🧠 MemoryVault is thinking..."
    ):

        result = memory_graph.invoke(
            graph_state
        )

    # ==================================================
    # GET RESULTS FROM GRAPH
    # ==================================================

    results = result.get(
        "retrieved_chunks",
        []
    )

    answer = result.get(
        "answer",
        ""
    )

    route = result.get(
        "route",
        "memory"
    )


    # ==================================================
    # DEBUG
    # ==================================================

    print("\n==============================")
    print("GRAPH RESULT DEBUG")
    print("==============================")
    print("Route:", route)
    print("Answer:", answer)
    print("Retrieved Chunks:", len(results))
    print("==============================")


    # ==================================================
    # NO ANSWER
    # ==================================================

    if not answer:

        st.error(
            "MemoryVault could not generate an answer."
        )

        return


    # ==================================================
    # MEMORY ROUTE — NO RESULTS
    # ==================================================

    if (
        route == "memory"
        and len(results) == 0
    ):

        st.info(
            "I could not find relevant information "
            "in your memories."
        )

        # Save the response as well
        db.save_message(
            conversation_id,
            "assistant",
            answer,
        )

        with st.chat_message("assistant"):

            st.markdown(answer)

        return


    # ==================================================
    # SAVE ASSISTANT MESSAGE
    # ==================================================

    db.save_message(
        conversation_id,
        "assistant",
        answer,
    )


    # ==================================================
    # SHOW ASSISTANT MESSAGE
    # ==================================================

    with st.chat_message("assistant"):

        st.markdown(answer)

    # ==================================================
    # RETRIEVED CHUNKS — DEBUG
    # ==================================================

    # ==================================================
    # SOURCES
    # ==================================================

    if results:

        with st.expander(
            "📚 Sources",
            expanded=False,
        ):

            shown_documents = set()

            for result in results:

                document_id = result.get(
                    "document_id"
                )

                filename = result.get(
                    "filename",
                    "Unknown document",
                )

                # ------------------------------------------
                # Avoid showing the same document repeatedly
                # ------------------------------------------

                if document_id in shown_documents:
                    continue

                shown_documents.add(
                    document_id
                )

                st.markdown(
                    f"📄 **{filename}**"
                )

                if document_id is not None:

                    st.caption(
                        f"Document ID: {document_id}"
                    )

                st.divider()