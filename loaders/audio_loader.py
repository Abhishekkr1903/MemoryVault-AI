"""
===============================================================================
File: audio_loader.py

Purpose
-------
This module transcribes uploaded audio files into text using faster-whisper.

Supported Formats
-----------------
✔ MP3
✔ WAV
✔ M4A
✔ OGG
✔ FLAC

Responsibilities
----------------
✔ Load Whisper model only once
✔ Transcribe uploaded audio
✔ Return standardized memory object

This module DOES NOT
--------------------
❌ Create embeddings
❌ Store data in database
❌ Call Gemini
❌ Create vector store
===============================================================================
"""

import tempfile
from pathlib import Path

from faster_whisper import WhisperModel


# Load the Whisper model once when the application starts.
MODEL = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8",
)


def transcribe_audio(audio_file) -> dict:
    """
    Transcribe an uploaded audio file into text.

    Parameters
    ----------
    audio_file
        Streamlit UploadedFile object.

    Returns
    -------
    dict

    Example
    -------
    {
        "text": "...",
        "source_type": "audio",
        "filename": "meeting.mp3"
    }

    Raises
    ------
    ValueError
        If no speech is detected.

    Exception
        If transcription fails.
    """

    with tempfile.NamedTemporaryFile(
        suffix=Path(audio_file.name).suffix,
        delete=False,
    ) as temp_file:

        temp_file.write(audio_file.getbuffer())
        temp_path = temp_file.name

    try:
        # Transcribe the audio
        segments, _ = MODEL.transcribe(temp_path)

        # Join all transcription segments
        transcribed_text = " ".join(
            segment.text for segment in segments
        ).strip()

        if not transcribed_text:
            raise ValueError("No speech detected in the audio file.")

        return {
            "text": transcribed_text,
            "source_type": "audio",
            "filename": audio_file.name,
        }

    except Exception as error:
        raise Exception(
            f"Audio transcription failed: {error}"
        ) from error

    finally:
        # Delete the temporary audio file
        Path(temp_path).unlink(missing_ok=True)