# ============================================================
# INTENT ROUTER
# ============================================================
#
# Decides whether a user query should be handled as:
#
#   chat   -> General conversation / general knowledge
#   memory -> Search the user's uploaded memories
#
# This is intentionally rule-based for now.
# ============================================================


# ============================================================
# MEMORY INTENT KEYWORDS
# ============================================================

MEMORY_PHRASES = [

    # --------------------------------------------------------
    # Personal memory
    # --------------------------------------------------------

    "my resume",
    "my cv",
    "my profile",
    "my experience",
    "my background",
    "my education",
    "my skills",
    "my projects",
    "my internship",
    "my internships",
    "my work experience",
    "my career",

    # --------------------------------------------------------
    # Personal information
    # --------------------------------------------------------

    "do you know me",
    "tell me about me",
    "tell me about myself",
    "what do you know about me",
    "who am i",
    "what is my name",

    # --------------------------------------------------------
    # Resume / career specific
    # --------------------------------------------------------

    "where did i intern",
    "where did i work",
    "where have i worked",
    "what companies did i work",
    "what companies have i worked",
    "which companies did i work",
    "which companies have i worked",
    "what projects did i work on",
    "what projects have i worked on",
    "what are my projects",
    "what are my skills",

    # --------------------------------------------------------
    # Documents
    # --------------------------------------------------------

    "this document",
    "this file",
    "this pdf",
    "this memory",
    "this document about",
    "what is this document",
    "what is this file",
    "what is this pdf",

    # --------------------------------------------------------
    # Memories
    # --------------------------------------------------------

    "my memories",
    "my memory",
    "uploaded memories",
    "uploaded memory",
    "uploaded documents",
    "uploaded files",
    "my documents",
    "my files",

    # --------------------------------------------------------
    # Research
    # --------------------------------------------------------

    "my research",
    "my research memories",
    "research memories",
    "research documents",
    "research notes",
    "my research notes",

    # --------------------------------------------------------
    # Information stored in MemoryVault
    # --------------------------------------------------------

    "what did i upload",
    "what have i uploaded",
    "what documents did i upload",
    "what files did i upload",
    "what information do you have about me",
]


# ============================================================
# MEMORY KEYWORDS
# ============================================================

MEMORY_KEYWORDS = [

    "resume",
    "cv",
    "internship",
    "internships",
    "experience",
    "education",
    "projects",
    "research",
    "memories",
    "memory",
    "uploaded",
    "document",
    "documents",
]


# ============================================================
# CHAT KEYWORDS
# ============================================================

CHAT_PHRASES = [

    "hi",
    "hello",
    "hey",
    "hii",
    "helo",

    "how are you",
    "how r you",
    "what's up",
    "whats up",

    "good morning",
    "good afternoon",
    "good evening",

    "nice to meet you",

    "thank you",
    "thanks",
    "thank",
    "you're welcome",
    "you are welcome",

    "bye",
    "goodbye",

    "who are you",
    "what is your name",
    "tell me about yourself",

]


# ============================================================
# HELPER
# ============================================================

def _normalize_question(question: str) -> str:
    """
    Normalize the user's question before routing.
    """

    if not question:
        return ""

    return " ".join(
        question.lower().strip().split()
    )


# ============================================================
# MEMORY INTENT DETECTOR
# ============================================================

def detect_memory_intent(question: str) -> bool:
    """
    Determine whether the question is asking about
    information stored in the user's memories.
    """

    q = _normalize_question(question)

    if not q:
        return False

    # --------------------------------------------------------
    # First check exact memory phrases
    # --------------------------------------------------------

    for phrase in MEMORY_PHRASES:

        if phrase in q:
            return True

    # --------------------------------------------------------
    # Check combinations of memory-related words
    #
    # Example:
    #
    # "tell me about my internship"
    # "what is in my resume"
    # --------------------------------------------------------

    has_personal_reference = any(
        word in q
        for word in [
            "my",
            "me",
            "i",
        ]
    )

    has_memory_keyword = any(
        word in q
        for word in MEMORY_KEYWORDS
    )

    if has_personal_reference and has_memory_keyword:
        return True

    # --------------------------------------------------------
    # Document-specific questions
    #
    # Example:
    #
    # "what is this document?"
    # "summarize this pdf"
    # --------------------------------------------------------

    document_words = [
        "document",
        "pdf",
        "file",
    ]

    document_question_words = [
        "what",
        "tell",
        "summarize",
        "summary",
        "explain",
        "describe",
        "about",
    ]

    has_document_word = any(
        word in q
        for word in document_words
    )

    has_document_question = any(
        word in q
        for word in document_question_words
    )

    if has_document_word and has_document_question:
        return True

    return False


# ============================================================
# CHAT INTENT DETECTOR
# ============================================================

def detect_chat_intent(question: str) -> bool:
    """
    Determine whether the question is ordinary conversation.
    """

    q = _normalize_question(question)

    if not q:
        return True

    for phrase in CHAT_PHRASES:

        if q == phrase or q.startswith(phrase):
            return True

    return False


# ============================================================
# MAIN ROUTER
# ============================================================

def route_query(question: str) -> str:
    """
    Route a user question.

    Returns
    -------
    str
        "memory" -> search uploaded memories
        "chat"    -> general conversation
    """

    q = _normalize_question(question)

    # --------------------------------------------------------
    # Empty question
    # --------------------------------------------------------

    if not q:
        return "chat"

    # --------------------------------------------------------
    # MEMORY HAS PRIORITY
    #
    # This is important.
    #
    # Example:
    #
    # "tell me about my internship"
    #
    # contains conversational language but should still
    # search memory.
    # --------------------------------------------------------

    if detect_memory_intent(q):

        return "memory"

    # --------------------------------------------------------
    # Normal conversation
    # --------------------------------------------------------

    if detect_chat_intent(q):

        return "chat"

    # --------------------------------------------------------
    # Default
    #
    # General questions should NOT search the user's
    # private memories unless the user explicitly refers
    # to them.
    # --------------------------------------------------------

    return "chat"


# ============================================================
# DEBUG TEST
# ============================================================

if __name__ == "__main__":

    test_questions = [

        "hi",

        "hello",

        "how are you",

        "what is 2+2",

        "what is Python",

        "explain machine learning",

        "tell me about my resume",

        "where did I intern",

        "what are my projects",

        "do you know me",

        "tell me about my research memories",

        "what is this document",

        "summarize this pdf",

        "what information do you have about me",

    ]

    print()
    print("=" * 60)
    print("INTENT ROUTER TEST")
    print("=" * 60)

    for question in test_questions:

        route = route_query(question)

        print(
            f"{question:<45} -> {route}"
        )

    print("=" * 60)