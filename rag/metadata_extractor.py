import json

from rag.model import generate


def extract_metadata(text):
    """
    Extract structured metadata from document text using Gemini.
    """

    prompt = f"""
You are an AI document analyzer.

Analyze the document below and return ONLY valid JSON.

Do not add:
- Markdown
- ```json
- Explanations
- Extra text

Return exactly this structure:

{{
    "category": "",
    "summary": "",
    "keywords": [],
    "language": ""
}}

Allowed categories:

- resume
- invoice
- receipt
- passport
- travel
- medical
- notes
- research
- book
- general

Rules:

1. category must be exactly one of the allowed categories.
2. summary should be a short description of the document.
3. keywords should contain important topics, names, technologies,
   entities, or concepts found in the document.
4. language should contain the primary language of the document.
5. keywords must be a JSON array of strings.
6. Return valid JSON only.

Document:

{text[:5000]}
"""

    response = generate(prompt)

    # ---------------------------------------
    # Try to parse Gemini's response
    # ---------------------------------------

    try:
        metadata = json.loads(response)

    except json.JSONDecodeError:

        # Sometimes an LLM may still return:
        # ```json
        # {...}
        # ```

        cleaned_response = response.strip()

        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]

        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]

        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]

        cleaned_response = cleaned_response.strip()

        try:
            metadata = json.loads(cleaned_response)

        except json.JSONDecodeError as error:
            raise ValueError(
                f"Gemini returned invalid metadata JSON:\n\n{response}"
            ) from error

    # ---------------------------------------
    # Validate required fields
    # ---------------------------------------

    required_fields = [
        "category",
        "summary",
        "keywords",
        "language",
    ]

    for field in required_fields:

        if field not in metadata:
            raise ValueError(
                f"Metadata is missing required field: {field}"
            )

    # ---------------------------------------
    # Normalize metadata
    # ---------------------------------------

    if not isinstance(metadata["keywords"], list):
        metadata["keywords"] = [
            str(metadata["keywords"])
        ]

    return metadata