import json
from collections import Counter

import streamlit as st

import database.db as db
from database.db import get_documents_with_metadata


# ==========================================================
# OPEN A NEW CHAT FOR A SPECIFIC MEMORY
# ==========================================================

def open_memory_chat(document_id, filename):
    """
    Open a brand-new conversation focused on one memory.

    This function is called when the user clicks:
    '💬 Chat with this Memory'
    """

    # ------------------------------------------------------
    # Select the memory
    # ------------------------------------------------------

    st.session_state.selected_document_id = document_id
    st.session_state.selected_filename = filename

    # ------------------------------------------------------
    # Restrict RAG search to the selected memory
    # ------------------------------------------------------

    st.session_state.search_scope = "Current Memory"

    # ------------------------------------------------------
    # Create a NEW conversation
    # ------------------------------------------------------

    conversation_id = db.create_conversation(
        title=f"Chat - {filename}"
    )

    st.session_state.conversation_id = conversation_id

    # ------------------------------------------------------
    # Update application navigation
    #
    # 'page' controls which page the application displays.
    # 'navigation_page' controls the sidebar radio button.
    # ------------------------------------------------------

    st.session_state.page = "Chat"
    st.session_state.navigation_page = "Chat"


# ==========================================================
# KEYWORD PARSER
# ==========================================================

def parse_keywords(keywords):
    """
    Convert the keywords stored in SQLite into a Python list.

    Keywords may be stored as:
        JSON string
        Python list
        plain string
        None
    """

    if not keywords:
        return []

    # Already a list
    if isinstance(keywords, list):
        return keywords

    # JSON string
    if isinstance(keywords, str):

        try:

            parsed = json.loads(keywords)

            if isinstance(parsed, list):
                return parsed

        except (json.JSONDecodeError, TypeError):

            pass

        # Fall back to treating the entire value
        # as one keyword.
        return [keywords]

    return []


# ==========================================================
# MEMORY DETAILS COMPONENT
# ==========================================================

def render_memory_details(document, key_suffix=""):
    """
    Render the details of one memory.

    Expected document tuple:

        0 -> id
        1 -> filename
        2 -> file_path
        3 -> created_at
        4 -> category
        5 -> summary
        6 -> keywords
        7 -> language
    """

    # ------------------------------------------------------
    # Extract database fields
    # ------------------------------------------------------

    document_id = document[0]
    filename = document[1]
    created_at = document[3]

    category = document[4]
    summary = document[5]
    keywords = document[6]
    language = document[7]

    # ------------------------------------------------------
    # Display friendly defaults
    # ------------------------------------------------------

    if not category:
        category = "General"

    if not language:
        language = "Unknown"

    # ------------------------------------------------------
    # Basic metadata
    # ------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        st.write(
            f"**Document ID:** {document_id}"
        )

        st.write(
            f"**Category:** {category}"
        )

        st.write(
            f"**Language:** {language}"
        )

    with col2:

        st.write(
            f"**Uploaded:** {created_at}"
        )

    st.divider()

    # ------------------------------------------------------
    # Summary
    # ------------------------------------------------------

    st.markdown("**Summary**")

    if summary:

        st.write(summary)

    else:

        st.caption(
            "No summary available."
        )

    # ------------------------------------------------------
    # Keywords
    # ------------------------------------------------------

    st.markdown("**Keywords**")

    keyword_list = parse_keywords(keywords)

    if keyword_list:

        st.write(
            ", ".join(
                str(keyword)
                for keyword in keyword_list
            )
        )

    else:

        st.caption(
            "No keywords available."
        )

    # ------------------------------------------------------
    # Chat button
    # ------------------------------------------------------

    st.divider()

    if st.button(
        "💬 Chat with this Memory",
        key=f"chat_memory_{document_id}_{key_suffix}",
        on_click=open_memory_chat,
        args=(document_id, filename),
    ):
        pass


# ==========================================================
# DASHBOARD
# ==========================================================

def render_dashboard():

    st.header("📊 MemoryVault Dashboard")

    # ======================================================
    # LOAD DOCUMENTS
    # ======================================================

    documents = get_documents_with_metadata()

    # ======================================================
    # BASIC SESSION INFORMATION
    # ======================================================

    current = st.session_state.get(
        "current_document"
    )

    selected = st.session_state.get(
        "selected_filename"
    )

    # ======================================================
    # DASHBOARD METRICS
    # ======================================================

    total_documents = len(documents)

    # Count categories
    category_counts = Counter()

    for document in documents:

        category = document[4]

        if category:
            category_counts[category] += 1

    unique_categories = len(
        category_counts
    )

    # ======================================================
    # FIND LATEST UPLOAD
    # ======================================================

    latest_upload = "None"

    if documents:

        dates = []

        for document in documents:

            # IMPORTANT:
            # document[3] = created_at
            created_at = document[3]

            if created_at:
                dates.append(created_at)

        if dates:
            latest_upload = max(dates)

    # ======================================================
    # METRIC CARDS
    # ======================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "📚 Total Memories",
            total_documents,
        )

    with col2:

        st.metric(
            "🏷️ Categories",
            unique_categories,
        )

    with col3:

        st.metric(
            "🕐 Latest Upload",
            latest_upload,
        )

    st.divider()

    # ======================================================
    # CURRENT SESSION
    # ======================================================

    st.subheader("Current Session")

    if selected:

        st.write(
            f"Selected memory: **{selected}**"
        )

    elif current:

        st.write(
            f"Last uploaded document: **{current}**"
        )

    else:

        st.write(
            "No document selected in this session."
        )

    # Number of chunks currently loaded
    chunk_count = len(
        st.session_state.get(
            "chunks",
            [],
        )
    )

    st.write(
        f"Chunks processed in this session: "
        f"**{chunk_count}**"
    )

    st.divider()

    # ======================================================
    # CATEGORY EXPLORER
    # ======================================================

    st.subheader("🏷️ Explore Categories")

    if not category_counts:

        st.info(
            "No categories available yet."
        )

    else:

        # --------------------------------------------------
        # Show available categories
        # --------------------------------------------------

        st.markdown(
            "Select a category to see the memories "
            "stored under it."
        )

        # Use a maximum of 4 columns per row.
        categories = sorted(
            category_counts.keys()
        )

        category_columns = st.columns(
            min(4, len(categories))
        )

        for index, category in enumerate(
            categories
        ):

            column = category_columns[
                index % len(category_columns)
            ]

            with column:

                st.metric(
                    category.title(),
                    category_counts[category],
                )

        # --------------------------------------------------
        # Category selector
        # --------------------------------------------------

        category_options = [
            "All Categories"
        ] + categories

        selected_category = st.selectbox(
            "🔎 Browse Category",
            category_options,
            key="dashboard_category",
        )

        # --------------------------------------------------
        # Filter memories
        # --------------------------------------------------

        if selected_category == "All Categories":

            filtered_documents = documents

        else:

            filtered_documents = [
                document
                for document in documents
                if (
                    document[4]
                    and document[4]
                    == selected_category
                )
            ]

        # --------------------------------------------------
        # Result count
        # --------------------------------------------------

        st.caption(
            f"{len(filtered_documents)} "
            f"memory/memories found"
        )

        # --------------------------------------------------
        # Display category memories
        # --------------------------------------------------

        if filtered_documents:

            for document in filtered_documents:

                filename = document[1]

                with st.expander(
                    f"📄 {filename}"
                ):

                    render_memory_details(
                        document,
                        key_suffix="category",
                    )

        else:

            st.info(
                "No memories found in this category."
            )

    st.divider()

    # ======================================================
    # ALL MEMORIES
    # ======================================================

    st.subheader("📚 Your Memories")

    if not documents:

        st.info(
            "No memories have been uploaded yet."
        )

        return

    # ------------------------------------------------------
    # Display every memory
    # ------------------------------------------------------

    for document in documents:

        document_id = document[0]
        filename = document[1]

        category = document[4]

        if not category:
            category = "General"

        # --------------------------------------------------
        # Memory header
        # --------------------------------------------------

        with st.expander(
            f"📄 {filename}  •  {category}"
        ):

            render_memory_details(
                document,
                key_suffix="all",
            )

# ==========================================================
# MEMORY TIMELINE
# ==========================================================

def render_timeline():
    """
    Render all memories in chronological order.

    Newest memories appear first.
    """

    st.header("🕒 Memory Timeline")

    # ------------------------------------------------------
    # Load memories
    # ------------------------------------------------------

    documents = get_documents_with_metadata()

    if not documents:
        st.info(
            "No memories have been stored yet. "
            "Drop a memory into MemoryVault to start your timeline."
        )
        return

    # ------------------------------------------------------
    # Sort by upload date
    # ------------------------------------------------------

    documents = sorted(
        documents,
        key=lambda document: document[3] or "",
        reverse=True,
    )

    st.caption(
        f"{len(documents)} memories in your MemoryVault"
    )

    st.divider()

    # ------------------------------------------------------
    # Timeline
    # ------------------------------------------------------

    for document in documents:

        document_id = document[0]
        filename = document[1]
        created_at = document[3]

        category = document[4] or "General"
        summary = document[5]
        keywords = document[6]
        language = document[7] or "Unknown"

        # --------------------------------------------------
        # Format date
        # --------------------------------------------------

        display_date = created_at or "Unknown date"

        if created_at:
            try:
                from datetime import datetime

                parsed_date = datetime.fromisoformat(
                    created_at
                )

                display_date = parsed_date.strftime(
                    "%d %b %Y • %I:%M %p"
                )

            except (ValueError, TypeError):
                display_date = str(created_at)

        # --------------------------------------------------
        # Timeline item
        # --------------------------------------------------

        st.markdown(
            f"### 🧠 {filename}"
        )

        st.caption(
            f"📅 {display_date}  •  "
            f"🏷️ {category}  •  "
            f"🌐 {language}"
        )

        # --------------------------------------------------
        # Summary
        # --------------------------------------------------

        if summary:
            st.write(summary)
        else:
            st.caption("No summary available.")

        # --------------------------------------------------
        # Keywords
        # --------------------------------------------------

        keyword_list = parse_keywords(keywords)

        if keyword_list:
            st.caption(
                "🔑 " +
                " • ".join(
                    str(keyword)
                    for keyword in keyword_list
                )
            )

        # --------------------------------------------------
        # Chat button
        # --------------------------------------------------

        if st.button(
            "💬 Chat with this Memory",
            key=f"timeline_chat_{document_id}",
            on_click=open_memory_chat,
            args=(document_id, filename),
        ):
            pass

        st.divider()


# ==========================================================
# MEMORY RECALL
# ==========================================================

def render_recall():
    """Render the Memory Recall page."""

    st.header("🧠 Memory Recall")

    st.caption(
        "Create reminders to revisit your memories later."
    )

    # ------------------------------------------------------
    # LOAD MEMORIES
    # ------------------------------------------------------

    documents = get_documents_with_metadata()

    if not documents:
        st.info(
            "No memories available. "
            "Store a memory first."
        )
        return

    # ------------------------------------------------------
    # CREATE RECALL
    # ------------------------------------------------------

    st.subheader("➕ Create Recall")

    document_options = {
        document[0]: document[1]
        for document in documents
    }

    selected_document_id = st.selectbox(
        "Select Memory",
        options=list(document_options.keys()),
        format_func=lambda document_id:
            document_options[document_id],
        key="recall_document",
    )

    recall_title = st.text_input(
        "What should I recall?",
        placeholder="e.g. Review my RAG architecture",
        key="recall_title",
    )

    col1, col2 = st.columns(2)

    from datetime import date, time

    with col1:

        recall_date = st.date_input(
            "📅 Recall Date",
            value=date.today(),
            key="recall_date",
        )

    with col2:

        recall_time = st.time_input(
            "⏰ Recall Time",
            value=time(9, 0),
            key="recall_time",
        )

    if st.button(
        "🧠 Create Recall",
        type="primary",
        use_container_width=True,
    ):

        if not recall_title.strip():

            st.warning(
                "Please enter what you want to recall."
            )

        else:

            recall_id = db.create_memory_recall(
                document_id=selected_document_id,
                title=recall_title.strip(),
                recall_date=recall_date.isoformat(),
                recall_time=recall_time.strftime(
                    "%H:%M"
                ),
            )

            st.success(
                "🧠 Recall created successfully!"
            )

            st.session_state.pop(
                "recall_title",
                None,
            )

            st.rerun()

    # ------------------------------------------------------
    # UPCOMING RECALLS
    # ------------------------------------------------------

    st.divider()

    st.subheader("🔔 Upcoming Recalls")

    pending_recalls = db.get_memory_recalls(
        status="pending"
    )

    if not pending_recalls:

        st.info(
            "No pending recalls."
        )

    else:

        for recall in pending_recalls:

            (
                recall_id,
                document_id,
                title,
                recall_date,
                recall_time,
                status,
                created_at,
                filename,
            ) = recall

            st.markdown(
                f"### 🔔 {title}"
            )

            st.caption(
                f"📅 {recall_date}  •  "
                f"⏰ {recall_time}"
            )

            st.caption(
                f"📄 Memory: {filename}"
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "✅ Complete",
                    key=f"complete_recall_{recall_id}",
                    use_container_width=True,
                ):

                    db.complete_memory_recall(
                        recall_id
                    )

                    st.rerun()

            with col2:

                if st.button(
                    "🗑 Delete",
                    key=f"delete_recall_{recall_id}",
                    use_container_width=True,
                ):

                    db.delete_memory_recall(
                        recall_id
                    )

                    st.rerun()

            st.divider()

    # ------------------------------------------------------
    # COMPLETED RECALLS
    # ------------------------------------------------------

    st.subheader("✅ Completed Recalls")

    completed_recalls = db.get_memory_recalls(
        status="completed"
    )

    if not completed_recalls:

        st.caption(
            "No completed recalls yet."
        )

    else:

        for recall in completed_recalls:

            (
                recall_id,
                document_id,
                title,
                recall_date,
                recall_time,
                status,
                created_at,
                filename,
            ) = recall

            st.markdown(
                f"~~{title}~~"
            )

            st.caption(
                f"📅 {recall_date}  •  "
                f"⏰ {recall_time}  •  "
                f"📄 {filename}"
            )

            if st.button(
                "🗑 Delete",
                key=f"delete_completed_{recall_id}",
            ):

                db.delete_memory_recall(
                    recall_id
                )

                st.rerun()