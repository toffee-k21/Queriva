from fastapi import FastAPI

from app.api.routes import documents
from app.api.routes import chat
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="Queriva",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    documents.router
)

app.include_router(
    chat.router
)


@app.get("/health")
def health_check():

    return {
        "status": "ok"
    }