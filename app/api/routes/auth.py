from chromadb.app import settings
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core.database import engine

from app.schemas.auth import Token, User
from sqlalchemy.orm import Session

from datetime import  timedelta
from typing import Annotated

from app.services.auth import authenticate_user, create_access_token





router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(form_data.email, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")



@router.post("/register")
def signup(request: User):
    # add vailadation for email and password
    if not request.email:
        raise HTTPException(status_code=400, detail="Email is required")
    if not request.password:
        raise HTTPException(status_code=400, detail="Password is required")
    
    with Session(engine) as session:
        newUser = User(
            name=request.name,
            email=request.email,
            password=request.password,
        )
        session.add_all([newUser])
        session.commit()

    return {
        "message": "User created successfully"
    }


