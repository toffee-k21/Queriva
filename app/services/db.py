
from app.models.document import Document
from app.core.database import engine
from sqlalchemy.orm import Session
from sqlalchemy import select

def insert_into_document_table(  
    filename:str,
    user_id:str
):
    with Session(engine) as session:
        new_document = Document(
            filename=filename,
            user_id=user_id
        )

        session.add(new_document)
        session.commit()
        session.refresh(new_document)
    return new_document.id

def get_documents_by_user_id(user_id: str):
    with Session(engine) as session:
        stmt = select(Document).where(
            Document.user_id == user_id
        )
        documents = session.scalars(stmt).all()

    return documents