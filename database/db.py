import sqlite3
import json
from pathlib import Path


# ==========================================================
# DATABASE CONFIGURATION
# ==========================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = (
    ROOT_DIR
    / "data"
    / "database"
    / "memoryvault.db"
)


# ==========================================================
# DATABASE CONNECTION
# ==========================================================

def get_connection():
    """Create a SQLite database connection."""

    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    # Enable foreign key support.
    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# ==========================================================
# DATABASE INITIALIZATION
# ==========================================================

def initialize_database():
    """Create required database tables if they do not exist."""

    connection = get_connection()
    cursor = connection.cursor()

    # ======================================================
    # DOCUMENTS TABLE
    # ======================================================

    # Older database files may lack newer columns,
    # so we create the base table and then migrate
    # additional columns separately.

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # ======================================================
    # CONVERSATIONS TABLE
    # ======================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT DEFAULT 'New Chat',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # ======================================================
    # MESSAGES TABLE
    # ======================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(conversation_id)
                REFERENCES conversations(id)
                ON DELETE CASCADE
        )
        """
    )

    # ======================================================
    # DOCUMENT SOURCE TYPE MIGRATION
    # ======================================================

    # Inspect the table schema and add source_type
    # if it is missing.

    cursor.execute(
        "PRAGMA table_info(documents)"
    )

    columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    if "source_type" not in columns:

        try:

            cursor.execute(
                """
                ALTER TABLE documents
                ADD COLUMN source_type TEXT
                DEFAULT 'pdf'
                """
            )

        except Exception:
            # If ALTER TABLE fails for any reason,
            # ignore and continue.
            pass

    # ======================================================
    # DOCUMENT METADATA MIGRATION
    # ======================================================

    cursor.execute(
        "PRAGMA table_info(documents)"
    )

    columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    new_columns = {
        "category": "TEXT",
        "summary": "TEXT",
        "keywords": "TEXT",
        "language": "TEXT",
    }

    for column, datatype in new_columns.items():

        if column not in columns:

            try:

                cursor.execute(
                    f"""
                    ALTER TABLE documents
                    ADD COLUMN {column} {datatype}
                    """
                )

            except Exception:
                pass

    # ======================================================
    # MEMORY RECALLS TABLE
    # ======================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS memory_recalls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            recall_date TEXT NOT NULL,
            recall_time TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(document_id)
                REFERENCES documents(id)
                ON DELETE CASCADE
        )
        """
    )

    # ======================================================
    # COMMIT DATABASE CHANGES
    # ======================================================

    connection.commit()
    connection.close()


# ==========================================================
# DOCUMENT FUNCTIONS
# ==========================================================

def get_document_by_filename(filename):
    """Return the document ID for a filename, or None if not found."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM documents
        WHERE filename = ?
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (filename,),
    )

    row = cursor.fetchone()

    connection.close()

    return row[0] if row else None


def save_document_record(
    filename,
    file_path,
    metadata=None,
):
    """
    Save uploaded document metadata to SQLite.
    """

    existing_id = get_document_by_filename(
        filename
    )

    if existing_id is not None:
        return existing_id

    # Default metadata if none is provided.
    if metadata is None:

        metadata = {
            "category": "general",
            "summary": "",
            "keywords": [],
            "language": "",
        }

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO documents
        (
            filename,
            file_path,
            category,
            summary,
            keywords,
            language
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            filename,
            file_path,
            metadata.get(
                "category",
                "general",
            ),
            metadata.get(
                "summary",
                "",
            ),
            json.dumps(
                metadata.get(
                    "keywords",
                    [],
                )
            ),
            metadata.get(
                "language",
                "",
            ),
        ),
    )

    document_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return document_id


def update_document_metadata(
    document_id,
    metadata,
):
    """
    Update AI-generated metadata for an existing document.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE documents
        SET
            category = ?,
            summary = ?,
            keywords = ?,
            language = ?
        WHERE id = ?
        """,
        (
            metadata.get(
                "category",
                "general",
            ),
            metadata.get(
                "summary",
                "",
            ),
            json.dumps(
                metadata.get(
                    "keywords",
                    [],
                )
            ),
            metadata.get(
                "language",
                "",
            ),
            document_id,
        ),
    )

    connection.commit()
    connection.close()


def get_all_documents():
    """Fetch all saved documents from SQLite."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            filename,
            file_path,
            created_at
        FROM documents
        ORDER BY created_at DESC
        """
    )

    documents = cursor.fetchall()

    connection.close()

    return documents


def get_unique_documents():
    """Fetch one latest row per filename to hide duplicates."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            filename,
            file_path,
            created_at
        FROM documents
        WHERE id IN (
            SELECT MAX(id)
            FROM documents
            GROUP BY filename
        )
        ORDER BY created_at DESC
        """
    )

    documents = cursor.fetchall()

    connection.close()

    return documents


def get_documents_with_metadata():
    """
    Return all documents along with their AI-generated metadata.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            filename,
            file_path,
            created_at,
            category,
            summary,
            keywords,
            language
        FROM documents
        ORDER BY created_at DESC
        """
    )

    documents = cursor.fetchall()

    connection.close()

    return documents


def delete_document(document_id):
    """Delete a document record from SQLite."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM documents
        WHERE id = ?
        """,
        (document_id,),
    )

    connection.commit()
    connection.close()


# ==========================================================
# AUDIO / IMAGE RECORDS
# ==========================================================

def save_audio_record(
    filename,
    file_path,
):
    """Save uploaded audio metadata to SQLite with source_type='audio'."""

    existing_id = get_document_by_filename(
        filename
    )

    if existing_id is not None:

        # Prevent duplicate audio records
        # for the same filename.
        return existing_id

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO documents (
            filename,
            file_path,
            source_type
        )
        VALUES (?, ?, ?)
        """,
        (
            filename,
            file_path,
            "audio",
        ),
    )

    document_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return document_id


def save_image_record(
    filename,
    file_path,
):
    """Save uploaded image metadata to SQLite with source_type='image'."""

    existing_id = get_document_by_filename(
        filename
    )

    if existing_id is not None:

        # Prevent duplicate image records
        # for the same filename.
        return existing_id

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO documents (
            filename,
            file_path,
            source_type
        )
        VALUES (?, ?, ?)
        """,
        (
            filename,
            file_path,
            "image",
        ),
    )

    document_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return document_id


# ==========================================================
# CONVERSATION FUNCTIONS
# ==========================================================

def create_conversation(
    title="New Chat",
):
    """Create a new conversation."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO conversations(title)
        VALUES(?)
        """,
        (title,),
    )

    conversation_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return conversation_id


def save_message(
    conversation_id,
    role,
    message,
):
    """Save one chat message."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO messages(
            conversation_id,
            role,
            message
        )
        VALUES(?,?,?)
        """,
        (
            conversation_id,
            role,
            message,
        ),
    )

    connection.commit()
    connection.close()


def get_messages(
    conversation_id,
):
    """Return all messages of one conversation."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            role,
            message,
            created_at
        FROM messages
        WHERE conversation_id=?
        ORDER BY id
        """,
        (conversation_id,),
    )

    messages = cursor.fetchall()

    connection.close()

    return messages


def get_conversation(
    conversation_id,
):
    """Return one conversation."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            title,
            created_at
        FROM conversations
        WHERE id = ?
        """,
        (conversation_id,),
    )

    conversation = cursor.fetchone()

    connection.close()

    return conversation


def get_conversations():
    """Return all conversations."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            title,
            created_at
        FROM conversations
        ORDER BY created_at DESC
        """
    )

    conversations = cursor.fetchall()

    connection.close()

    return conversations


def delete_conversation(
    conversation_id,
):
    """Delete one conversation."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM conversations
        WHERE id=?
        """,
        (conversation_id,),
    )

    connection.commit()
    connection.close()


def rename_conversation(
    conversation_id,
    title,
):
    """Rename a conversation."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE conversations
        SET title=?
        WHERE id=?
        """,
        (
            title,
            conversation_id,
        ),
    )

    connection.commit()
    connection.close()


def clear_messages(
    conversation_id,
):
    """Delete all messages from one conversation."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM messages
        WHERE conversation_id = ?
        """,
        (conversation_id,),
    )

    connection.commit()
    connection.close()


# ==========================================================
# MEMORY RECALL FUNCTIONS
# ==========================================================

def create_memory_recall(
    document_id,
    title,
    recall_date,
    recall_time,
):
    """
    Create a new memory recall.

    Parameters
    ----------
    document_id : int
        ID of the memory/document.

    title : str
        Recall/reminder text.

    recall_date : str
        Date in YYYY-MM-DD format.

    recall_time : str
        Time in HH:MM format.

    Returns
    -------
    int
        ID of the newly created recall.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO memory_recalls (
            document_id,
            title,
            recall_date,
            recall_time,
            status
        )
        VALUES (?, ?, ?, ?, 'pending')
        """,
        (
            document_id,
            title,
            recall_date,
            recall_time,
        ),
    )

    recall_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return recall_id


def get_memory_recalls(
    status=None,
):
    """
    Get memory recalls along with their memory filename.

    If status is provided, only recalls with that status
    are returned.

    Returns rows in this format:

        (
            id,
            document_id,
            title,
            recall_date,
            recall_time,
            status,
            created_at,
            filename
        )
    """

    connection = get_connection()
    cursor = connection.cursor()

    if status:

        cursor.execute(
            """
            SELECT
                r.id,
                r.document_id,
                r.title,
                r.recall_date,
                r.recall_time,
                r.status,
                r.created_at,
                d.filename
            FROM memory_recalls r
            JOIN documents d
                ON r.document_id = d.id
            WHERE r.status = ?
            ORDER BY
                r.recall_date ASC,
                r.recall_time ASC
            """,
            (status,),
        )

    else:

        cursor.execute(
            """
            SELECT
                r.id,
                r.document_id,
                r.title,
                r.recall_date,
                r.recall_time,
                r.status,
                r.created_at,
                d.filename
            FROM memory_recalls r
            JOIN documents d
                ON r.document_id = d.id
            ORDER BY
                r.recall_date ASC,
                r.recall_time ASC
            """
        )

    recalls = cursor.fetchall()

    connection.close()

    return recalls


def complete_memory_recall(
    recall_id,
):
    """
    Mark a memory recall as completed.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE memory_recalls
        SET status = 'completed'
        WHERE id = ?
        """,
        (recall_id,),
    )

    connection.commit()
    connection.close()


def delete_memory_recall(
    recall_id,
):
    """
    Delete a memory recall.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM memory_recalls
        WHERE id = ?
        """,
        (recall_id,),
    )

    connection.commit()
    connection.close()