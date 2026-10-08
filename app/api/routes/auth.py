
from app.core.config import settings
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core.database import engine

from app.schemas.auth import Token, User
from sqlalchemy.orm import Session

from datetime import  timedelta
from typing import Annotated

from app.services.auth import authenticate_user, create_access_token, get_current_user, get_password_hash
from app.models.user import User as UserModel
from app.schemas.auth import Token, User


router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    # form_data.username is actually the email, as we are using email as the username
    user = authenticate_user(form_data.username, form_data.password)
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



@router.post("/register", status_code=status.HTTP_201_CREATED)
def signup(request: User):
    if not request.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )

    if not request.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required"
        )

    hashed_password = get_password_hash(request.password)

    with Session(engine) as session:
        new_user = UserModel(
            name=request.name,
            email=request.email,
            hashed_password=hashed_password,
        )

        session.add(new_user)
        session.commit()
        session.refresh(new_user)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
            data={"sub": request.email}, expires_delta=access_token_expires
        )
    return Token(access_token=access_token, token_type="bearer")

@router.get("/users/me/")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user