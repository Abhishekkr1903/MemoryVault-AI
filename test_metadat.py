from rag.metadata_extractor import extract_metadata

text = """
Machine Learning is a field of artificial intelligence.
It uses algorithms such as linear regression,
logistic regression and decision trees.
Python and SQL are commonly used in data science.
"""

metadata = extract_metadata(text)

print(metadata)