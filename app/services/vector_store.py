import chromadb


client = chromadb.PersistentClient(
    path="./storage/chroma"
)


collection = client.get_or_create_collection(
    name="documents"
)


def add_chunks(
    chunks,
    embeddings,
    document_id
):

    ids = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):

        ids.append(
            f"{document_id}_chunk_{i}"
        )

        documents.append(
            chunk["text"]
        )

        metadatas.append({
            "page": chunk["page"],
            "document_id": document_id
        })

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )


def search(
    query_embedding,
    document_ids,
    top_k=5
):

    return collection.query(
        query_embeddings=[query_embedding],

        n_results=top_k,

        where={
            "document_id": {
                "$in": document_ids
            }
        },

        include=[
            "documents",
            "metadatas"
        ]
    )