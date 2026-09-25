from app.services.embeddings import create_embedding
from app.services.vector_store import search
from sentence_transformers import CrossEncoder

reranker = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

def retrieve(
    question,
    document_ids,
    top_k=20
):

    query_embedding = create_embedding(
        question
    )

    results = search(
        query_embedding,
        document_ids,
        top_k
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    if not documents:
        return []

    # Re-rank candidates
    pairs = [(question, doc) for doc in documents]

    scores = reranker.predict(pairs)

    ranked_docs = sorted(
        zip(documents, scores, metadatas),
        key=lambda x: x[1],
        reverse=True
    )

    return [
        (doc, metadata) for doc, score, metadata in ranked_docs[:top_k]
    ]