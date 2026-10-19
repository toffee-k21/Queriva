from app.services.embeddings import tokenizer

CHUNK_SIZE = 200
CHUNK_OVERLAP = 40


def create_chunks(
    pages,
    chunk_size=CHUNK_SIZE,
    overlap=CHUNK_OVERLAP,
):
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap must be >= 0 and < chunk_size")

    chunks = []
    step = chunk_size - overlap

    for page in pages:
        text = page["text"].strip()

        if not text:
            continue

        # Tokenize text for chunk-size calculation
        token_ids = tokenizer.encode(
            text,
            add_special_tokens=False,
        )

        start = 0

        while start < len(token_ids):
            end = min(start + chunk_size, len(token_ids))
            chunk_ids = token_ids[start:end]

            # Convert the token window back into readable text
            chunk_text = tokenizer.decode(
                chunk_ids,
                skip_special_tokens=True,
            ).strip()

            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "page": page["page"],
                })

            if end == len(token_ids):
                break

            start += step

    return chunks