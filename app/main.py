from fastapi import FastAPI

from app.api.routes import documents
from app.api.routes import chat


app = FastAPI(
    title="Queriva",
    version="1.0.0"
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