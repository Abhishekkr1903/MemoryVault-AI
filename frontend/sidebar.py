import shutil
from pathlib import Path

import streamlit as st

import database.db as db
import rag.vectorstore as vectorstore


def render_sidebar():
    """
    Render the MemoryVault sidebar.

    The sidebar manages:
    - Saved memories
    - Conversations
    - Search scope
    - Memory selection
    - Application navigation
    - Current memory
    - Memory deletion

    IMPORTANT:
    Only the Memories and Conversations lists are scrollable.
    The overall sidebar remains fixed.
    """

    # ==========================================================
    # LOAD SAVED MEMORIES
    # ==========================================================

    documents = db.get_unique_documents()

    # ----------------------------------------------------------
    # Automatically select the first memory if none is selected
    # ----------------------------------------------------------

    if (
        documents
        and "selected_document_id" not in st.session_state
    ):
        first_doc = documents[0]

        st.session_state.selected_document_id = first_doc[0]

    # ==========================================================
    # INITIALIZE SESSION STATE
    # ==========================================================

    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = None

    if "selected_document_ids" not in st.session_state:
        st.session_state.selected_document_ids = []

    if "search_scope" not in st.session_state:
        st.session_state.search_scope = "Current Memory"

    if "page" not in st.session_state:
        st.session_state.page = "Chat"

    # ==========================================================
    # MEMORIES
    # ==========================================================

    st.sidebar.header("📂 Memories")

    # ----------------------------------------------------------
    # IMPORTANT:
    # Fixed-height container.
    #
    # If there are many memories, ONLY this area scrolls.
    # ----------------------------------------------------------

    memory_container = st.sidebar.container(
        height=220,
        border=False,
    )

    with memory_container:

        if documents:

            for document in documents:

                document_id, filename, _, created_at = document

                st.write(
                    f"📄 **{filename}**"
                )

                st.caption(
                    f"Uploaded: {created_at}"
                )

        else:

            st.info(
                "No memories uploaded."
            )

    # ==========================================================
    # CONVERSATIONS
    # ==========================================================

    st.sidebar.markdown("---")

    st.sidebar.header("💬 Conversations")

    # ----------------------------------------------------------
    # NEW CHAT BUTTON
    # ----------------------------------------------------------

    if st.sidebar.button(
        "➕ New Chat",
        use_container_width=True,
    ):

        conversation_id = db.create_conversation()

        st.session_state.conversation_id = (
            conversation_id
        )

        # Navigate to Chat
        st.session_state.page = "Chat"

        # Keep navigation radio synchronized
        st.session_state.navigation_page = "Chat"

        st.rerun()

    # ----------------------------------------------------------
    # LOAD CONVERSATIONS
    # ----------------------------------------------------------

    conversations = db.get_conversations()

    # ----------------------------------------------------------
    # Automatically select first conversation
    # ----------------------------------------------------------

    if (
        st.session_state.conversation_id is None
        and conversations
    ):

        st.session_state.conversation_id = (
            conversations[0][0]
        )

        st.session_state.page = "Chat"

        st.session_state.navigation_page = "Chat"

    # ----------------------------------------------------------
    # SCROLLABLE CONVERSATION AREA
    # ----------------------------------------------------------

    conversation_container = st.sidebar.container(
        height=220,
        border=False,
    )

    with conversation_container:

        if conversations:

            current_conversation = (
                st.session_state.get(
                    "conversation_id"
                )
            )

            for conversation in conversations:

                conversation_id, title, _ = conversation

                label = title

                # Highlight active conversation
                if (
                    conversation_id
                    == current_conversation
                ):
                    label = f"🟢 {title}"

                col1, col2 = st.columns(
                    [6, 1]
                )

                # --------------------------------------------------
                # OPEN CONVERSATION
                # --------------------------------------------------

                with col1:

                    if st.button(
                        label,
                        key=f"conversation_{conversation_id}",
                        use_container_width=True,
                    ):

                        st.session_state.conversation_id = (
                            conversation_id
                        )

                        st.session_state.page = "Chat"

                        st.session_state.navigation_page = (
                            "Chat"
                        )

                        st.rerun()

                # --------------------------------------------------
                # DELETE CONVERSATION
                # --------------------------------------------------

                with col2:

                    if st.button(
                        "🗑",
                        key=f"delete_{conversation_id}",
                        use_container_width=True,
                    ):

                        db.delete_conversation(
                            conversation_id
                        )

                        # ------------------------------------------
                        # If deleted conversation was active
                        # ------------------------------------------

                        if (
                            st.session_state.conversation_id
                            == conversation_id
                        ):

                            remaining = (
                                db.get_conversations()
                            )

                            if remaining:

                                st.session_state.conversation_id = (
                                    remaining[0][0]
                                )

                            else:

                                # Create fresh conversation
                                new_id = (
                                    db.create_conversation()
                                )

                                st.session_state.conversation_id = (
                                    new_id
                                )

                        st.rerun()

        else:

            st.caption(
                "No conversations yet."
            )

    # ==========================================================
    # SEARCH SCOPE
    # ==========================================================

    st.sidebar.markdown("---")

    st.sidebar.subheader(
        "🔍 Search Scope"
    )

    search_scopes = [
        "Current Memory",
        "Selected Memories",
        "All Memories",
    ]

    st.session_state.search_scope = (
        st.sidebar.radio(
            "Search scope",
            search_scopes,
            index=search_scopes.index(
                st.session_state.search_scope
            ),
            key="search_scope_radio",
            label_visibility="collapsed",
        )
    )

    # ==========================================================
    # MEMORY SELECTION
    # ==========================================================

    selected_ids = []

    if (
        st.session_state.search_scope
        == "Selected Memories"
    ):

        st.sidebar.markdown(
            "##### Select Memories"
        )

        # ------------------------------------------------------
        # Keep selection area inside the Memories scroll area
        # logically by limiting the displayed list.
        #
        # We don't create another large sidebar section here.
        # ------------------------------------------------------

        for document in documents:

            document_id = document[0]
            filename = document[1]

            checked = st.sidebar.checkbox(
                filename,
                key=f"memory_{document_id}",
            )

            if checked:
                selected_ids.append(
                    document_id
                )

    st.session_state.selected_document_ids = (
        selected_ids
    )

    # ==========================================================
    # NAVIGATION
    # ==========================================================

    st.sidebar.markdown("---")

    navigation_pages = [
        "Upload",
        "Chat",
        "Dashboard",
        "Timeline",
        "Recall",
    ]

    # ----------------------------------------------------------
    # Initialize navigation state
    # ----------------------------------------------------------

    if "navigation_page" not in st.session_state:

        st.session_state.navigation_page = (
            st.session_state.page
        )

    # ----------------------------------------------------------
    # Navigation radio
    # ----------------------------------------------------------

    page = st.sidebar.radio(
        "Navigation",
        navigation_pages,
        key="navigation_page",
    )

    st.session_state.page = page

    # ==========================================================
    # CURRENT MEMORY
    # ==========================================================

    if documents:

        st.sidebar.markdown("---")

        st.sidebar.subheader(
            "📄 Current Memory"
        )

        # ------------------------------------------------------
        # Determine currently selected memory
        # ------------------------------------------------------

        current_index = 0

        selected_id = (
            st.session_state.get(
                "selected_document_id"
            )
        )

        for i, doc in enumerate(documents):

            if doc[0] == selected_id:

                current_index = i

                break

        # ------------------------------------------------------
        # Memory selector
        # ------------------------------------------------------

        selected_document = (
            st.sidebar.selectbox(
                "Load Memory",
                documents,
                index=current_index,
                format_func=lambda doc: doc[1],
            )
        )

        # ------------------------------------------------------
        # Load selected memory
        # ------------------------------------------------------

        if selected_document:

            document_id, filename, _, _ = (
                selected_document
            )

            chunks, embeddings, index = (
                vectorstore.load_vectorstore(
                    document_id
                )
            )

            # --------------------------------------------------
            # Vectorstore does not exist
            # --------------------------------------------------

            if chunks is None or index is None:

                st.sidebar.warning(
                    "Vectorstore not found."
                )

                return page

            # --------------------------------------------------
            # Store current memory information
            # --------------------------------------------------

            st.session_state.selected_document_id = (
                document_id
            )

            st.session_state.selected_filename = (
                filename
            )

            st.session_state.chunks = chunks

            st.session_state.index = index

            st.sidebar.caption(
                f"Current Memory: {filename}"
            )

            # ==================================================
            # DELETE MEMORY
            # ==================================================

            if st.sidebar.button(
                "🗑 Delete Memory",
                use_container_width=True,
            ):

                # ----------------------------------------------
                # Delete database record
                # ----------------------------------------------

                db.delete_document(
                    document_id
                )

                # ----------------------------------------------
                # Delete vectorstore
                # ----------------------------------------------

                shutil.rmtree(
                    Path("data/vectorstore")
                    / str(document_id),
                    ignore_errors=True,
                )

                # ----------------------------------------------
                # Clear related session state
                # ----------------------------------------------

                for key in [
                    "selected_document_id",
                    "selected_filename",
                    "selected_document_ids",
                    "chunks",
                    "index",
                ]:

                    st.session_state.pop(
                        key,
                        None,
                    )

                st.rerun()

    # ==========================================================
    # RETURN CURRENT PAGE
    # ==========================================================

    return page