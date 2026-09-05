"""
===============================================================================
File: pdf_loader.py

Purpose
-------
This module is responsible ONLY for extracting readable text from PDF files.

Responsibilities
----------------
✔ Read uploaded PDF files.
✔ Extract text from every page.
✔ Ignore empty pages.
✔ Return a standardized dictionary that the rest of the application can use.

This module DOES NOT:
---------------------
❌ Create embeddings
❌ Chunk text
❌ Store data in the database
❌ Call the LLM

Keeping a single responsibility makes the project easier to maintain.
===============================================================================
"""

from typing import BinaryIO

from pypdf import PdfReader


def extract_text_from_pdf(pdf_file: BinaryIO) -> dict:
    """
    Extract readable text from an uploaded PDF.

    Parameters
    ----------
    pdf_file : BinaryIO
        Uploaded PDF file received from Streamlit.

    Returns
    -------
    dict
        Standardized memory object.

        Example:
        {
            "text": "...",
            "source_type": "pdf",
            "filename": "notes.pdf"
        }

    Raises
    ------
    ValueError
        If no readable text is found in the PDF.

    Exception
        If the PDF cannot be opened or read.
    """

    try:
        # Create a PDF reader object.
        # PdfReader allows us to access every page individually.
        reader = PdfReader(pdf_file)

        # Store extracted text from each page.
        page_texts = []

        # Loop through every page in the PDF.
        for page_number, page in enumerate(reader.pages, start=1):

            # Extract readable text.
            # For scanned PDFs this may return None.
            text = page.extract_text()

            # Ignore empty pages.
            if text and text.strip():
                page_texts.append(text.strip())

        # Combine all page text into one document.
        full_text = "\n\n".join(page_texts)

        # Raise an error if no text could be extracted.
        if not full_text:
            raise ValueError(
                "No readable text found. The PDF may be scanned or image-based."
            )

        # Return a standardized object.
        return {
            "text": full_text,
            "source_type": "pdf",
            "filename": getattr(pdf_file, "name", "uploaded_document.pdf"),
        }

    except Exception as error:
        raise Exception(f"Failed to extract text from PDF: {error}") from error