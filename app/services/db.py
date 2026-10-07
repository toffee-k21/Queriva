
from app.models.document import Document
from app.core.database import engine
from sqlalchemy.orm import Session

def insert_into_document_table(
    document_id:str,    
    filename:str,
    user_id:str
):
    """Insert a document into the database."""

    with Session(engine) as session:
        new_document = Document(
            document_id=document_id,
            filename=filename,
            user_id=user_id
        )

        session.add(new_document)
        session.commit()