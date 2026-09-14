from pydantic import BaseModel


class ChatRequest(BaseModel):

    document_ids: list[str]

    question: str