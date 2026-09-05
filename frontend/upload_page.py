import streamlit as st
from pathlib import Path
import database.db as db

import re

from loaders.pdf_loader import extract_text_from_pdf
from loaders.audio_loader import transcribe_audio
from loaders.image_loader import extract_text_from_image

from rag.chunking import chunk_text
from rag.embeddings import create_embeddings
from rag.vectorstore import create_faiss_index, save_vectorstore
from rag.metadata_extractor import extract_metadata

from database.db import (
    save_document_record,
    save_audio_record,
    save_image_record,
    update_document_metadata,
)

def generate_memory_name(text: str) -> str:
    """
    Generate a clean local name for a direct text memory.

    No Gemini/API call is used.
    """

    text = " ".join(text.strip().split())

    if not text:
        return "Untitled Memory"

    # Take the first sentence if available
    sentences = re.split(
        r"(?<=[.!?])\s+",
        text,
    )

    title = sentences[0].strip()

    # If first sentence is too long, use first 8 words
    if len(title) > 60:
        title = " ".join(
            text.split()[:8]
        )

    # Remove unwanted filename characters
    title = re.sub(
        r'[<>:"/\\|?*]',
        "",
        title,
    )

    title = title.strip(" .")

    if not title:
        title = "Untitled Memory"

    return title[:60]


# ==========================================================
# MEMORY DROP
# ==========================================================

# ==========================================================
# MEMORY DROP
# ==========================================================

def render_upload_page():
    """
    Render the Memory Drop page.

    Memory Drop supports:

        📄 PDF
        📝 TXT
        🖼️ Image
        🎧 Audio

    Users can drop multiple files at once.

    Files are NOT automatically processed when selected.

    The user explicitly clicks:
        "🧠 Store Memories"

    Each file is then routed to the appropriate
    ingestion function.
    """

    st.header("🧠 Memory Drop")

    st.caption(
        "Drop your memories here. "
        "Store them now and chat with them anytime later."
    )

    # ======================================================
    # DIRECT TEXT MEMORY
    # ======================================================

    input_type = st.radio(
        "What do you want to drop?",
        [
            "📁 Files",
            "📝 Text",
        ],
        horizontal=True,
    )

    # ======================================================
    # DIRECT TEXT
    # ======================================================

    if input_type == "📝 Text":

        text_memory = st.text_area(
            "Write or paste your memory",
            height=250,
            placeholder=(
                "Write anything you want MemoryVault "
                "to remember..."
            ),
        )

        if st.button(
            "🧠 Store Memory",
            type="primary",
            use_container_width=True,
        ):

            if not text_memory.strip():

                st.warning(
                    "Please enter some text first."
                )

                return

            # --------------------------------------------------
            # Create unique filename
            # --------------------------------------------------

            from datetime import datetime

            timestamp = datetime.now().strftime(
                "%Y%m%d_%H%M%S_%f"
            )

            memory_name = generate_memory_name(
                text_memory
            )

            filename = f"{memory_name}.txt"

            physical_filename = (
                f"text_memory_{timestamp}.txt"
            )

            # --------------------------------------------------
            # Create upload directory
            # --------------------------------------------------

            upload_dir = Path(
                "data/uploads"
            )

            upload_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            file_path = (
                upload_dir / physical_filename
            )

            # --------------------------------------------------
            # Save text
            # --------------------------------------------------

            try:

                with open(
                    file_path,
                    "w",
                    encoding="utf-8",
                ) as file:

                    file.write(
                        text_memory
                    )

                # --------------------------------------------------
                # Create database record
                # --------------------------------------------------

                document_id = save_document_record(
                    filename=filename,
                    file_path=str(file_path),
                )

                # --------------------------------------------------
                # Common RAG pipeline
                # --------------------------------------------------

                process_and_store_text(
                    extracted_text=text_memory,
                    document_id=document_id,
                    filename=filename,
                )

            except Exception as error:

                st.error(
                    f"Could not store this memory:\n\n{error}"
                )

        return

    # ======================================================
    # FILE MEMORY
    # ======================================================

    uploaded_files = st.file_uploader(
        "Drop your memories here",
        type=[
            # --------------------------------------------------
            # PDF
            # --------------------------------------------------
            "pdf",

            # --------------------------------------------------
            # Text
            # --------------------------------------------------
            "txt",

            # --------------------------------------------------
            # Images
            # --------------------------------------------------
            "png",
            "jpg",
            "jpeg",
            "bmp",
            "webp",

            # --------------------------------------------------
            # Audio
            # --------------------------------------------------
            "mp3",
            "wav",
            "m4a",
            "ogg",
            "flac",
        ],
        accept_multiple_files=True,
    )

    # ======================================================
    # NO FILES
    # ======================================================

    if not uploaded_files:

        st.info(
            "Supported: PDF • Text • Image • Audio"
        )

        st.caption(
            "You can drop multiple memories at once."
        )

        return

    # ======================================================
    # SHOW SELECTED FILES
    # ======================================================

    st.subheader(
        f"📦 {len(uploaded_files)} "
        f"memory/memories selected"
    )

    for uploaded_file in uploaded_files:

        extension = Path(
            uploaded_file.name
        ).suffix.lower()

        # --------------------------------------------------
        # File icon
        # --------------------------------------------------

        if extension == ".pdf":

            icon = "📄"

        elif extension == ".txt":

            icon = "📝"

        elif extension in [
            ".png",
            ".jpg",
            ".jpeg",
            ".bmp",
            ".webp",
        ]:

            icon = "🖼️"

        elif extension in [
            ".mp3",
            ".wav",
            ".m4a",
            ".ogg",
            ".flac",
        ]:

            icon = "🎧"

        else:

            icon = "📁"

        st.write(
            f"{icon} **{uploaded_file.name}**"
        )

    # ======================================================
    # IMAGE PREVIEWS
    # ======================================================

    image_files = [
        file
        for file in uploaded_files
        if Path(file.name).suffix.lower()
        in [
            ".png",
            ".jpg",
            ".jpeg",
            ".bmp",
            ".webp",
        ]
    ]

    if image_files:

        with st.expander(
            "🖼️ Preview Images"
        ):

            for image_file in image_files:

                st.image(
                    image_file,
                    caption=image_file.name,
                    use_container_width=True,
                )

    # ======================================================
    # STORE ALL MEMORIES
    # ======================================================

    if st.button(
        "🧠 Store Memories",
        type="primary",
        use_container_width=True,
    ):

        st.divider()

        st.subheader(
            "📥 Processing Memories"
        )

        total_files = len(
            uploaded_files
        )

        successful = 0
        failed = 0

        # --------------------------------------------------
        # Process every selected file
        # --------------------------------------------------

        for index, uploaded_file in enumerate(
            uploaded_files,
            start=1,
        ):

            st.write(
                f"### {index}/{total_files} "
                f"— {uploaded_file.name}"
            )

            extension = Path(
                uploaded_file.name
            ).suffix.lower()

            try:

                # --------------------------------------------------
                # Check if this memory already exists
                # --------------------------------------------------

                existing_memories = {
                    document[1]
                    for document in db.get_unique_documents()
                }

                if uploaded_file.name in existing_memories:

                    st.warning(
                        f"⚠️ A memory named "
                        f"'{uploaded_file.name}' already exists. "
                        f"Skipping this file."
                    )

                    failed += 1

                    continue

                # --------------------------------------------------
                # Process file
                # --------------------------------------------------

                if extension == ".pdf":

                    process_pdf(
                        uploaded_file
                    )

                # ------------------------------------------
                # TXT
                # ------------------------------------------

                elif extension == ".txt":

                    process_text_file(
                        uploaded_file
                    )

                # ------------------------------------------
                # IMAGE
                # ------------------------------------------

                elif extension in [
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".bmp",
                    ".webp",
                ]:

                    process_image(
                        uploaded_file
                    )

                # ------------------------------------------
                # AUDIO
                # ------------------------------------------

                elif extension in [
                    ".mp3",
                    ".wav",
                    ".m4a",
                    ".ogg",
                    ".flac",
                ]:

                    process_audio(
                        uploaded_file
                    )

                else:

                    st.warning(
                        f"Unsupported file: "
                        f"{uploaded_file.name}"
                    )

                    failed += 1
                    continue

                successful += 1

            except Exception as error:

                failed += 1

                st.error(
                    f"❌ Failed to process "
                    f"{uploaded_file.name}:\n\n"
                    f"{error}"
                )

            st.divider()

        # ==================================================
        # FINAL RESULT
        # ==================================================

        if successful:

            st.success(
                f"🧠 {successful} "
                f"memory/memories stored successfully!"
            )

        if failed:

            st.warning(
                f"⚠️ {failed} "
                f"memory/memories could not be stored."
            )

        st.info(
            "Your memories are now stored. "
            "You can come back anytime and chat with them "
            "from the Chat page."
        )

# ==========================================================
# SAVE UPLOADED FILE
# ==========================================================

def save_uploaded_file(uploaded_file):
    """
    Save an uploaded file under data/uploads.

    Returns:
        Path to the saved file.

    Raises:
        FileExistsError if the file already exists.
    """

    upload_dir = Path("data/uploads")

    upload_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    saved_file_path = (
        upload_dir / uploaded_file.name
    )

    if saved_file_path.exists():
        raise FileExistsError(
            f"A memory named '{uploaded_file.name}' already exists."
        )

    with open(
        saved_file_path,
        "wb",
    ) as file:

        file.write(
            uploaded_file.getbuffer()
        )

    return saved_file_path


# ==========================================================
# PDF
# ==========================================================
def process_pdf(uploaded_file):
    """
    Process a PDF memory.

    PDF
      ↓
    Save
      ↓
    Database
      ↓
    Extract text
      ↓
    Common RAG pipeline
    """

    st.subheader("📄 PDF Memory")

    try:

        # --------------------------------------------------
        # Save file
        # --------------------------------------------------

        saved_file_path = save_uploaded_file(
            uploaded_file
        )

        # --------------------------------------------------
        # Create database record
        # --------------------------------------------------

        document_id = save_document_record(
            filename=uploaded_file.name,
            file_path=str(saved_file_path),
        )

        # --------------------------------------------------
        # Extract text
        # --------------------------------------------------

        with st.spinner(
            "📄 Extracting text from PDF..."
        ):

            memory = extract_text_from_pdf(
                saved_file_path
            )

        extracted_text = memory["text"]

        # --------------------------------------------------
        # Common pipeline
        # --------------------------------------------------

        process_and_store_text(
            extracted_text=extracted_text,
            document_id=document_id,
            filename=memory["filename"],
        )

    except FileExistsError as error:

        st.warning(
            f"⚠️ {error}"
        )

    except Exception as error:

        st.error(
            f"Could not process this PDF:\n\n{error}"
        )

# ==========================================================
# TEXT FILE
# ==========================================================
def process_text_file(uploaded_file):
    """
    Process a TXT memory.

    TXT
      ↓
    Save
      ↓
    Database
      ↓
    Read text
      ↓
    Common RAG pipeline
    """

    st.subheader("📝 Text Memory")

    try:

        # --------------------------------------------------
        # Save file
        # --------------------------------------------------

        saved_file_path = save_uploaded_file(
            uploaded_file
        )

        # --------------------------------------------------
        # Create database record
        # --------------------------------------------------

        document_id = save_document_record(
            filename=uploaded_file.name,
            file_path=str(saved_file_path),
        )

        # --------------------------------------------------
        # Read text
        # --------------------------------------------------

        with st.spinner(
            "📝 Reading text..."
        ):

            extracted_text = (
                uploaded_file
                .getvalue()
                .decode(
                    "utf-8",
                    errors="replace",
                )
            )

        # --------------------------------------------------
        # Preview
        # --------------------------------------------------

        with st.expander(
            "View text"
        ):

            st.write(
                extracted_text
            )

        # --------------------------------------------------
        # Common pipeline
        # --------------------------------------------------

        process_and_store_text(
            extracted_text=extracted_text,
            document_id=document_id,
            filename=uploaded_file.name,
        )

    except FileExistsError as error:

        st.warning(
            f"⚠️ {error}"
        )

    except Exception as error:

        st.error(
            f"Could not process this text file:\n\n{error}"
        )
# ==========================================================
# IMAGE
# ==========================================================
def process_image(uploaded_file):
    """
    Process an image memory.

    IMAGE
      ↓
    OCR
      ↓
    Text
      ↓
    Common RAG pipeline
    """

    st.subheader("🖼️ Image Memory")

    st.image(
        uploaded_file,
        caption=uploaded_file.name,
        use_container_width=True,
    )

    try:

        # --------------------------------------------------
        # Save image
        # --------------------------------------------------

        saved_file_path = save_uploaded_file(
            uploaded_file
        )

        # --------------------------------------------------
        # Create database record
        # --------------------------------------------------

        document_id = save_image_record(
            filename=uploaded_file.name,
            file_path=str(saved_file_path),
        )

        # --------------------------------------------------
        # OCR
        # --------------------------------------------------

        with st.spinner(
            "🔎 Extracting text from image..."
        ):

            memory = extract_text_from_image(
                uploaded_file
            )

        extracted_text = memory["text"]

        st.success(
            "Image text extracted successfully!"
        )

        # --------------------------------------------------
        # Show extracted text
        # --------------------------------------------------

        with st.expander(
            "View extracted text"
        ):

            st.write(
                extracted_text
            )

        # --------------------------------------------------
        # Common pipeline
        # --------------------------------------------------

        process_and_store_text(
            extracted_text=extracted_text,
            document_id=document_id,
            filename=memory["filename"],
        )

    except FileExistsError as error:

        st.warning(
            f"⚠️ {error}"
        )

    except Exception as error:

        st.error(
            f"Could not process this image:\n\n{error}"
        )


# ==========================================================
# AUDIO
# ==========================================================

def process_audio(uploaded_file):
    """
    Process an audio memory.

    AUDIO
      ↓
    Transcription
      ↓
    Text
      ↓
    Common RAG pipeline
    """

    st.subheader("🎧 Audio Memory")

    try:

        # --------------------------------------------------
        # Save audio
        # --------------------------------------------------

        saved_file_path = save_uploaded_file(
            uploaded_file
        )

        # --------------------------------------------------
        # Create database record
        # --------------------------------------------------

        document_id = save_audio_record(
            filename=uploaded_file.name,
            file_path=str(saved_file_path),
        )

        # --------------------------------------------------
        # Transcribe
        # --------------------------------------------------

        with st.spinner(
            "🎧 Transcribing audio..."
        ):

            memory = transcribe_audio(
                uploaded_file
            )

        extracted_text = memory["text"]

        st.success(
            "Audio transcribed successfully!"
        )

        # --------------------------------------------------
        # Show transcript
        # --------------------------------------------------

        with st.expander(
            "View transcribed text"
        ):

            st.write(
                extracted_text
            )

        # --------------------------------------------------
        # Common pipeline
        # --------------------------------------------------

        process_and_store_text(
            extracted_text=extracted_text,
            document_id=document_id,
            filename=memory["filename"],
        )

    except FileExistsError as error:

        st.warning(
            f"⚠️ {error}"
        )

    except Exception as error:

        st.error(
            f"Could not process this audio:\n\n{error}"
        )


# ==========================================================
# COMMON MEMORY PROCESSING PIPELINE
# ==========================================================

def process_and_store_text(
    extracted_text,
    document_id,
    filename,
):
    """
    Common processing pipeline for ALL memory types.

    PDF:
        PDF → text → here

    Text:
        TXT → text → here

    Image:
        Image → OCR → text → here

    Audio:
        Audio → transcription → text → here

    After text is obtained, every memory follows
    exactly the same RAG pipeline:

        Text
         ↓
        AI Metadata
         ↓
        Chunking
         ↓
        Embeddings
         ↓
        FAISS
         ↓
        Save Vectorstore
    """

    # ======================================================
    # VALIDATE TEXT
    # ======================================================

    if not extracted_text or not extracted_text.strip():

        st.warning(
            "No text could be extracted from this memory."
        )

        return

    # ======================================================
    # STEP 1 — AI METADATA
    # ======================================================

    metadata = None

    try:

        with st.spinner(
            "🧠 Understanding your memory..."
        ):

            metadata = extract_metadata(
                extracted_text
            )

        # --------------------------------------------------
        # Save metadata to SQLite
        # --------------------------------------------------

        update_document_metadata(
            document_id=document_id,
            metadata=metadata,
        )

        st.success(
            "AI metadata generated successfully!"
        )

        # --------------------------------------------------
        # Display metadata
        # --------------------------------------------------

        with st.expander(
            "🏷️ View AI Metadata"
        ):

            st.write(
                f"**Category:** "
                f"{metadata.get('category', 'general')}"
            )

            st.write(
                f"**Language:** "
                f"{metadata.get('language', '')}"
            )

            st.write(
                f"**Summary:** "
                f"{metadata.get('summary', '')}"
            )

            st.write(
                "**Keywords:**"
            )

            st.write(
                ", ".join(
                    metadata.get(
                        "keywords",
                        [],
                    )
                )
            )

    except Exception as error:

        # --------------------------------------------------
        # Metadata failure should NOT stop RAG processing.
        # --------------------------------------------------

        st.warning(
            f"Could not generate AI metadata: {error}"
        )

    # ======================================================
    # STEP 2 — CHUNKING
    # ======================================================

    with st.spinner(
        "✂️ Chunking memory..."
    ):

        chunks = chunk_text(
            extracted_text
        )

    if not chunks:

        st.error(
            "No chunks were created from this memory."
        )

        return

    # ======================================================
    # STEP 3 — EMBEDDINGS
    # ======================================================

    with st.spinner(
        "🔢 Creating embeddings..."
    ):

        embeddings = create_embeddings(
            chunks
        )

    # ======================================================
    # STEP 4 — FAISS INDEX
    # ======================================================

    with st.spinner(
        "🗂️ Creating vector store..."
    ):

        index = create_faiss_index(
            embeddings
        )

    # ======================================================
    # STEP 5 — SAVE VECTORSTORE
    # ======================================================

    save_vectorstore(
        document_id=document_id,
        chunks=chunks,
        embeddings=embeddings,
        index=index,
    )

    # ======================================================
    # STEP 6 — SESSION STATE
    # ======================================================

    st.session_state.chunks = chunks

    st.session_state.index = index

    st.session_state.current_document = (
        filename
    )

    st.session_state.document_id = (
        document_id
    )

    st.session_state.selected_document_id = (
        document_id
    )

    st.session_state.selected_filename = (
        filename
    )

    # ======================================================
    # SUCCESS
    # ======================================================
    # ======================================================
    # SUCCESS
    # ======================================================

    st.success(
        f"🧠 Memory successfully stored! "
        f"{len(chunks)} chunks indexed."
    )


    # ======================================================
    # DEBUG — VIEW CHUNKS
    # ======================================================

    with st.expander("📄 View Chunks"):

        for i, chunk in enumerate(
            chunks,
            start=1,
        ):

            st.markdown(
                f"### Chunk {i}"
            )

            st.write(chunk)

            st.divider()