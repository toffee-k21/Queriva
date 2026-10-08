from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None


class User(BaseModel):
    name: str
    email: str | None = None
    password: str

class UserInDB(BaseModel):
    id: int
    name: str
    email: str | None = None
    hashed_password: str