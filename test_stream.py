from rag.model import generate_stream


question = "Explain what Machine Learning is in 3 sentences."


print()
print("=" * 60)
print("STREAMING TEST")
print("=" * 60)
print()


for chunk in generate_stream(question):

    print(chunk, end="", flush=True)


print()
print()
print("=" * 60)