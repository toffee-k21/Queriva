
from fastapi import HTTPException, UploadFile

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_FILES = 5


async def validate_pdf_uploads(
    files: list[UploadFile],
) -> list[tuple[UploadFile, bytes]]:

    if not files:
        raise HTTPException(
            status_code=400,
            detail="At least one PDF file is required",
        )

    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_FILES} files allowed",
        )

    validated_files = []

    for file in files:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Only .pdf files are allowed",
            )

        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail="Invalid MIME type. Only PDFs are allowed",
            )

        content = await file.read(MAX_FILE_SIZE + 1)

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File size must not exceed 10 MB",
            )

        if not content.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file signature",
            )

        validated_files.append((file, content))

    return validated_files
