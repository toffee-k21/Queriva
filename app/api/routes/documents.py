from typing import Annotated
import uuid
import os

from fastapi import APIRouter, Depends, UploadFile, File

from app.schemas.auth import User, UserInDB
from app.services.auth import get_current_user
from app.services.pdf import extract_pdf
from app.services.chunker import create_chunks
from app.services.embeddings import create_embedding
from app.services.vector_store import add_chunks
from app.services.db import insert_into_document_table


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

@router.post("/upload")
async def upload_pdfs(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    files: list[UploadFile] = File(...),
):

    uploaded_documents = []


    for file in files:

        document_id = str(uuid.uuid4())

        os.makedirs(
            "data/uploads",
            exist_ok=True
        )

        pdf_path = (
            f"data/uploads/{document_id}.pdf"
        )

        # Save PDF
        with open(pdf_path, "wb") as f:
            f.write(await file.read())

        # Extract
        pages = extract_pdf(pdf_path)

        # Chunk
        chunks = create_chunks(pages)

        # Embeddings
        embeddings = [
            create_embedding(chunk["text"])
            for chunk in chunks
        ]

        # Store in vector DB
        add_chunks(
            chunks=chunks,
            embeddings=embeddings,
            document_id=document_id,
            filename=file.filename
        )

        uploaded_documents.append({
            "document_id": document_id,
            "filename": file.filename,
            "chunks": len(chunks)
        })

        insert_into_document_table(
            document_id=document_id,
            filename=file.filename,
            user_id=current_user.id
        )

    return {
        "documents": uploaded_documents
    }