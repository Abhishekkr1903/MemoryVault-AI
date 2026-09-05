"""
Determine whether a user query contains
metadata-based search intent.
"""


def detect_metadata_intent(question):
    """
    Detect simple metadata-related intent
    from the user's question.

    Returns
    -------
    str | None
        Detected category or None.
    """

    question_lower = question.lower()

    # Research-related queries
    if any(
        word in question_lower
        for word in [
            "research",
            "researches",
            "research memory",
            "research memories",
        ]
    ):
        return "research"

    return None