import streamlit as st

from database.db import get_all_documents


def render_memory_selector():
    """
    Show memory selection UI.

    Returns:
        search_scope (str)
        selected_document_ids (list)
    """

    st.sidebar.subheader("🔍 Search Scope")

    search_scope = st.sidebar.radio(
        "",
        [
            "Current Memory",
            "Selected Memories",
            "All Memories",
        ],
    )

    selected_document_ids = []

    # Show checkboxes only when needed.
    if search_scope == "Selected Memories":

        st.sidebar.markdown("### Select Memories")

        documents = get_all_documents()

        for document in documents:

            document_id = document[0]
            filename = document[1]

            if st.sidebar.checkbox(filename, key=f"doc_{document_id}"):

                selected_document_ids.append(document_id)

    return search_scope, selected_document_ids