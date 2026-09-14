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
async def upload_pdfs(
    files: list[UploadFile] = File(...)
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

    return {
        "documents": uploaded_documents
    }