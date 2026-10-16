from typing_extensions import Annotated
from fastapi import APIRouter, Depends
from app.schemas.chat import ChatRequest
from app.schemas.auth import UserInDB
from app.services.auth import get_current_user, verify_user_ownership
from app.services.retriever import retrieve
from app.services.generator import generate_answer


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.post("/")
def chat(request: ChatRequest,  current_user: Annotated[UserInDB, Depends(get_current_user)]):
    if not verify_user_ownership(current_user.id, request.document_ids):
        return {
            "error": "You do not have permission to access one or more of the specified documents."
        }
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