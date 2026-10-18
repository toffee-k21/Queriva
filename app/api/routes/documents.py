import asyncio
from typing import Annotated
import os
import logging
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.schemas.auth import UserInDB
from app.services.auth import get_current_user
from app.services.pdf import extract_pdf
from app.services.chunker import create_chunks
from app.services.embeddings import create_embedding
from app.services.vector_store import add_chunks, delete_document_chunks
from app.services.db import insert_into_document_table, delete_document, get_documents_by_user_id
from app.services.file_validation import validate_pdf_uploads


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

@router.post("/upload")
async def upload_pdfs(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    files: Annotated[list[UploadFile], File()]
):

    validated_files = await validate_pdf_uploads(files)

    uploaded_documents = []

    for file, content in validated_files:

        document_id = insert_into_document_table(
            filename=file.filename,
            user_id=current_user.id
        )

        if document_id is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to create document record"
            )


        pdf_path = (
            f"data/uploads/{document_id}.pdf"
        )

        try:
            os.makedirs(
                "data/uploads",
                exist_ok=True
            )

            # Save PDF
            with open(pdf_path, "wb") as f:
                f.write(content)
        
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
            await asyncio.sleep(10)
        except Exception as e:
            # Clean up vector-store writes
            try:
                delete_document_chunks(document_id)
            except Exception:
                logging.exception("Failed to clean up ChromaDB")

            # Delete saved PDF
            try:
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
            except OSError:
                logging.exception("Failed to delete uploaded PDF")

            # Delete SQL row
            try:
                delete_document(document_id)
            except Exception:
                logging.exception("Failed to delete SQL document row")

            
            raise HTTPException(
                status_code=500,
                detail="Failed to process uploaded PDF"
            ) from e
        finally:
            try:
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
            except OSError:
                logging.exception(
                    "Failed to delete temporary uploaded PDF: %s",
                    pdf_path
                )

    return {
        "documents": uploaded_documents
    }

@router.get("/list")
async def list_documents(
    current_user: Annotated[UserInDB, Depends(get_current_user)]
):

    documents = get_documents_by_user_id(current_user.id)

    return {
        "documents": documents
    }