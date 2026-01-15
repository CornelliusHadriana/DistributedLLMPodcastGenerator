import nltk
from typing import List

# Ensure the punkt tokenizer is available
nltk.download('punkt', quiet=True)

def chunk_by_sentence(text: str, target: int=200) -> List[str]:
    """
    Split text into chunks of approximately `target` words using sentence boundaries.
    Handles None/empty input gracefully by returning an empty list.
    """
    if not text:
        return []

    # Ensure we have a string
    if not isinstance(text, str):
        text = str(text)

    try:
        sentences = nltk.sent_tokenize(text)
    except Exception:
        return []

    chunks = []
    current = []
    word_count = 0

    for sentence in sentences:
        sentence_words = sentence.split()

        if word_count + len(sentence_words) > target:
            chunks.append(' '.join(current))
            current = []
            word_count = 0

        current.append(sentence)
        word_count += len(sentence_words)

    if current:
        chunks.append(' '.join(current))

    return chunks