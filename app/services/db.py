
from app.models.document import Document
from app.core.database import engine
from sqlalchemy.orm import Session

def insert_into_document_table(  
    filename:str,
    user_id:str
):
    """Insert a document into the database."""

    with Session(engine) as session:
        new_document = Document(
            filename=filename,
            user_id=user_id
        )

        session.add(new_document)
        session.commit()
        session.refresh(new_document)
    return new_document.id