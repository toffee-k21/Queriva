from app.services.embeddings import create_embedding
from app.services.vector_store import search


def retrieve(
    question,
    document_id,
    top_k=5
):

    query_embedding = create_embedding(
        question
    )

    results = search(
        query_embedding,
        document_id,
        top_k
    )

    return (
        results["documents"][0],
        results["metadatas"][0]
    )