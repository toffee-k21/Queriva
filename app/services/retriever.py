from app.services.embeddings import create_embedding
from app.services.vector_store import search
from app.services.query_expansion import expand_query
from sentence_transformers import CrossEncoder
import json

reranker = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)


def retrieve(
    question,
    document_ids,
    candidate_k=20,
    top_k=5
):
    # Step 1: Generate expanded queries
    queries = expand_query(question)

    # Step 2: Retrieve candidates for every query
    candidates = {}

    for query in queries:
        query_embedding = create_embedding(query)

        #   Retrive relevent chunks with relevent document_id
        results = search(
            query_embedding,
            document_ids,
            candidate_k
        )

        chunks = results["chunks"]
        metadatas = results["metadatas"]

        for chunk, metadata in zip(chunks, metadatas):
            # Deduplicate the same chunk retrieved by multiple queries
            key = (
                chunk,
                json.dumps(metadata, sort_keys=True)
            )

            if key not in candidates:
                candidates[key] = {
                    "chunk": chunk,
                    "metadata": metadata
                }

    if not candidates:
        return [], []

    # Step 3: Rerank candidates against the original and
    # expanded queries.
    items = list(candidates.values())
    chunks = [item["chunk"] for item in items]
    metadatas = [item["metadata"] for item in items]

    pairs = [
        (question, chunk)
        for chunk in chunks
    ]

    scores = reranker.predict(pairs)

    ranked = sorted(
        zip(chunks, metadatas, scores),
        key=lambda item: item[2],
        reverse=True
    )

    # Step 4: Return top-ranked chunks and their metadata
    return (
        [chunk for chunk, metadata, score in ranked[:top_k]],
        [metadata for chunk, metadata, score in ranked[:top_k]]
    )