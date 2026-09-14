import uuid
import os

from fastapi import APIRouter, UploadFile, File

from app.services.pdf import extract_pdf
from app.services.chunker import create_chunks
from app.services.embeddings import create_embedding
from app.services.vector_store import add_chunks


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...)
):

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

        f.write(
            await file.read()
        )


    # Extract text

    pages = extract_pdf(
        pdf_path
    )


    # Create chunks

    chunks = create_chunks(
        pages
    )


    # Create embeddings

    embeddings = [
        create_embedding(
            chunk["text"]
        )
        for chunk in chunks
    ]


    # Store in ChromaDB

    add_chunks(
        chunks,
        embeddings,
        document_id
    )


    return {
        "document_id": document_id,
        "chunks": len(chunks)
    }