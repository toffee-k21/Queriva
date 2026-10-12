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

        results = search(
            query_embedding,
            document_ids,
            candidate_k
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]

        for doc, metadata in zip(documents, metadatas):
            # Deduplicate the same chunk retrieved by multiple queries
            key = (
                doc,
                json.dumps(metadata, sort_keys=True)
            )

            if key not in candidates:
                candidates[key] = {
                    "document": doc,
                    "metadata": metadata
                }

    if not candidates:
        return [], []

    # Step 3: Rerank candidates against the original and
    # expanded queries.
    items = list(candidates.values())
    documents = [item["document"] for item in items]
    metadatas = [item["metadata"] for item in items]

    pairs = [
        (query, doc)
        for doc in documents
        for query in queries
    ]

    scores = reranker.predict(pairs)

    # Each document has one score per query.
    scores_by_document = [
        max(scores[i * len(queries):(i + 1) * len(queries)])
        for i in range(len(documents))
    ]

    ranked = sorted(
        zip(documents, metadatas, scores_by_document),
        key=lambda item: item[2],
        reverse=True
    )

    # Step 4: Return top-ranked chunks and their metadata
    return (
        [doc for doc, metadata, score in ranked[:top_k]],
        [metadata for doc, metadata, score in ranked[:top_k]]
    )