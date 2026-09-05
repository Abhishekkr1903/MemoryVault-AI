"""
===============================================================================
File: image_loader.py

Purpose
-------
This module is responsible for extracting readable text from images using
EasyOCR.

Supported Inputs
----------------
✔ JPG
✔ JPEG
✔ PNG
✔ BMP
✔ WEBP

Responsibilities
----------------
✔ Load the EasyOCR model only once.
✔ Accept either:
    - Streamlit uploaded files
    - Local image paths
✔ Extract text from the image.
✔ Return a standardized dictionary.

This module DOES NOT:
---------------------
❌ Create embeddings
❌ Chunk text
❌ Save to database
❌ Call Gemini
❌ Perform RAG

Keeping this module focused on one responsibility makes the project easier
to maintain and extend.
===============================================================================
"""

from functools import lru_cache
from pathlib import Path
from typing import Union
import tempfile

import easyocr
from PIL import Image


# -----------------------------------------------------------------------------
# Cache the OCR model.
#
# EasyOCR is a deep learning model and takes several seconds to initialize.
# We only want to load it ONCE when the application starts.
#
# Without caching:
#
# Upload Image
#      ↓
# Load Model (3-5 sec)
#      ↓
# OCR
#
# Every upload would reload the model.
#
# With @lru_cache:
#
# First Upload
#      ↓
# Load Model
#
# Second Upload
#      ↓
# Reuse Existing Model
#
# Much faster.
# -----------------------------------------------------------------------------
@lru_cache(maxsize=1)
def get_ocr_reader() -> easyocr.Reader:
    """
    Load the EasyOCR model.

    Returns
    -------
    easyocr.Reader
        Cached OCR model.
    """
    return easyocr.Reader(["en"], gpu=False)


# -----------------------------------------------------------------------------
# Main OCR Function
# -----------------------------------------------------------------------------
def extract_text_from_image(image_source) -> dict:
    """
    Extract readable text from an image.

    Parameters
    ----------
    image_source
        Can be either:

        1. Streamlit UploadedFile
        2. Local image path
        3. pathlib.Path object

    Returns
    -------
    dict

    Example

    {
        "text": "...",
        "source_type": "image",
        "filename": "notes.png"
    }

    Raises
    ------
    ValueError
        If no readable text exists.

    Exception
        If OCR fails.
    """

    temporary_file_created = False

    try:

        # ---------------------------------------------------------
        # Case 1
        #
        # User uploads an image from Streamlit.
        #
        # EasyOCR expects a file path, not an UploadedFile object.
        #
        # Therefore we temporarily save the uploaded image.
        # ---------------------------------------------------------
        if not isinstance(image_source, (str, Path)):

            suffix = Path(image_source.name).suffix

            with tempfile.NamedTemporaryFile(
                suffix=suffix,
                delete=False
            ) as temp_file:

                temp_file.write(image_source.getbuffer())
                image_path = temp_file.name

            temporary_file_created = True

        # ---------------------------------------------------------
        # Case 2
        #
        # User already provided an image path.
        # ---------------------------------------------------------
        else:
            image_path = str(image_source)

        # ---------------------------------------------------------
        # Open the image once.
        #
        # Converting to RGB prevents problems with:
        #
        # PNG
        # RGBA
        # Palette images
        #
        # We don't actually use the image object afterwards.
        # This simply verifies that the image is valid.
        # ---------------------------------------------------------
        Image.open(image_path).convert("RGB").close()

        # Load cached OCR model.
        reader = get_ocr_reader()

        # Extract text.
        results = reader.readtext(
            image_path,
            detail=0,
            paragraph=True
        )

        extracted_text = "\n".join(results).strip()

        if not extracted_text:
            raise ValueError("No readable text found in the image.")

        return {
            "text": extracted_text,
            "source_type": "image",
            "filename": Path(image_path).name,
        }

    except Exception as error:
        raise Exception(f"Image OCR failed: {error}") from error

    finally:

        # ---------------------------------------------------------
        # Remove temporary file.
        #
        # We DO NOT delete user files.
        #
        # We only delete files that WE created temporarily.
        # ---------------------------------------------------------
        if temporary_file_created:
            Path(image_path).unlink(missing_ok=True)