from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    name: str | None = None


class User(BaseModel):
    name: str
    email: str | None = None
    hashed_password: str
    