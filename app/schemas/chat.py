from pydantic import BaseModel


class ChatRequest(BaseModel):

    document_ids: list[int]

    question: str