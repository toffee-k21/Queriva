from fastapi import APIRouter

from app.schemas.auth import User

from app.services.retriever import retrieve
from app.services.generator import generate_answer


router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


@router.post("/signup")
def chat(request: User):
    
    

    return {
        
    }

