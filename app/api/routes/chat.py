from fastapi import APIRouter

from app.schemas.chat import ChatRequest

from app.services.retriever import retrieve
from app.services.generator import generate_answer


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.post("/")
def chat(request: ChatRequest):

    documents, metadatas = retrieve(
        request.question,
        request.document_ids
    )


    answer = generate_answer(
        request.question,
        documents,
        metadatas
    )


    sources = []

    for metadata in metadatas:

        sources.append({
            "filename": metadata["filename"],
            "page": metadata["page"]
        })

    return {
        "answer": answer,
        "sources": sources
    }