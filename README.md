# Queriva

Queriva is a backend for asking questions about selected PDF documents. It extracts text from uploaded PDFs, splits that text into overlapping chunks, embeds the chunks, stores them in ChromaDB, retrieves relevant chunks for a question, reranks the candidates, and uses a local Ollama model to generate an answer. The API also includes user registration, bearer-token authentication, and a document-list endpoint.

## Contents

- [What it does](#what-it-does)
- [Architecture](#architecture)
- [Request flows](#request-flows)
- [Retrieval details](#retrieval-details)
- [Data models and structures](#data-models-and-structures)
- [API endpoints](#api-endpoints)
- [Project layout](#project-layout)
- [Configuration](#configuration)
- [Run locally](#run-locally)
- [Database migrations](#database-migrations)
- [Implementation notes and current limitations](#implementation-notes-and-current-limitations)
- [Retrieval experiment](#retrieval-experiment)

## What it does

- Accepts one or more uploaded files through `POST /documents/upload`.
- Extracts non-empty page text with PyMuPDF (`fitz`).
- Splits each page's text into 1,000-character chunks with 200-character overlap by default.
- Creates embeddings with SentenceTransformers' `all-MiniLM-L6-v2` model.
- Stores chunk text and metadata in a persistent ChromaDB collection.
- Expands a question into additional search queries using the local Ollama model `qwen3:4b`.
- Searches only the selected document IDs, deduplicates retrieved chunks, reranks them with `cross-encoder/ms-marco-MiniLM-L-6-v2`, and sends the top results to Ollama for answer generation.
- Stores user and uploaded-document metadata in a SQL database through SQLAlchemy.
- Uses password hashing and JWT bearer tokens for the authentication routes.

## Architecture

```text
Client
  |
  v
FastAPI application (app/main.py)
  |-- /auth/*       -> authentication routes -> auth service -> SQLAlchemy -> SQL database
  |-- /documents/*  -> document routes
  |                    |-> auth dependency
  |                    |-> SQL document record
  |                    |-> save PDF under data/uploads/
  |                    |-> PyMuPDF page extraction
  |                    |-> character chunking
  |                    |-> SentenceTransformer embeddings
  |                    '--> ChromaDB persistent collection
  |
  '-- /chat/        -> chat route
                       |-> query expansion (Ollama qwen3:4b)
                       |-> query embeddings (SentenceTransformer)
                       |-> ChromaDB search filtered by document IDs
                       |-> CrossEncoder reranking
                       '--> answer generation (Ollama qwen3:4b)
```

### Main components

| Component | Responsibility |
|---|---|
| FastAPI (`app/main.py`) | Creates the app, configures CORS, includes routers, and exposes `/health`. |
| API routes (`app/api/routes/`) | Define HTTP endpoints and connect request data to service functions. |
| Pydantic schemas (`app/schemas/`) | Define request/response-related data shapes used by the API and authentication flow. |
| SQLAlchemy models (`app/models/`) | Define `users` and `documents` relational tables. |
| Core (`app/core/`) | Loads environment configuration, creates the SQLAlchemy engine/base, and defines the OAuth2 bearer-token scheme. |
| Services (`app/services/`) | Implement authentication, PDF extraction, chunking, embedding, vector storage, retrieval, query expansion, and generation. |
| Alembic (`alembic/`) | Holds database migration configuration and migration scripts. |
| `app/ab_testing_rag.py` | Standalone experiment that sends an entire PDF's extracted text directly to the LLM; it is not called by the API routes. |

## Request flows

### 1. Upload and index PDFs

The implemented route is `POST /documents/upload`.

1. FastAPI resolves `get_current_user` from the bearer token. The route expects a list of uploaded files.
2. For each file, `insert_into_document_table()` creates a `Document` row using the original filename and current user's ID, then returns the new row's integer ID.
3. The route creates `data/uploads/` if it does not exist and writes the uploaded bytes to `data/uploads/<document_id>.pdf`.
4. `extract_pdf()` opens that saved path with PyMuPDF. It iterates through pages, strips page text, and returns only pages whose text is non-empty. Page numbers in this result are one-based.
5. `create_chunks()` splits each page's text into character windows. Its defaults are `chunk_size=1000` and `overlap=200`; the next window starts 800 characters after the previous start.
6. `create_embedding()` encodes each chunk's text with `all-MiniLM-L6-v2` and converts the resulting array to a Python list.
7. `add_chunks()` creates one ChromaDB record per chunk. Its ID is `<document_id>_chunk_<zero-based chunk index>`. Metadata includes `page`, `document_id`, and `filename`; chunk text is stored as the document.
8. The route returns a `documents` array with each document's ID, original filename, and number of chunks.

The SQL record and vector records are stored separately: document metadata is in the SQL database, while chunk text and metadata are in ChromaDB. The original PDF is written to the local `data/uploads/` directory.

### 2. List a user's documents

The `GET /documents/list` route also depends on `get_current_user`. It calls `get_documents_by_user_id(current_user.id)`, which selects `Document` rows whose `user_id` matches the current user's ID, and returns them under the `documents` key.

### 3. Ask a question about selected documents

The implemented route is `POST /chat/` and expects a `ChatRequest` containing `document_ids` and `question`.

1. The route calls `retrieve(question, document_ids)`.
2. `expand_query()` asks Ollama (`qwen3:4b`) for 3–4 concise alternative search queries and requests JSON output. The original question is retained, duplicate strings are removed, and at most five queries are returned. If parsing fails or the response has an unexpected shape, the original question is used.
3. Each query is embedded with `create_embedding()` and sent to `search()` with `candidate_k=20`.
4. `search()` queries the ChromaDB `documents` collection, asking for document text and metadata and applying a metadata filter where `document_id` is in the selected ID list.
5. Candidate chunks returned by multiple queries are deduplicated using a key made from the chunk text and a sorted JSON representation of its metadata.
6. The CrossEncoder scores each candidate against every expanded query. The implementation keeps the maximum score for each candidate, sorts candidates in descending score order, and returns at most `top_k=5` chunks with their metadata.
7. `generate_answer()` formats the selected chunks with their page numbers into a context string, then calls Ollama (`qwen3:4b`) with a prompt instructing it to answer from the supplied context and not invent unsupported facts.
8. The route returns the generated `answer` and a `sources` array containing each returned metadata record's `filename` and `page`.

The source list is built from the metadata returned by retrieval. The code does not currently deduplicate the final `sources` array separately.

## Retrieval details

The retrieval implementation is split across three files:

- `app/services/query_expansion.py`: expands the original question with Ollama and parses the response as JSON.
- `app/services/vector_store.py`: stores and searches embeddings in the persistent ChromaDB collection.
- `app/services/retriever.py`: orchestrates expansion, semantic retrieval, candidate deduplication, CrossEncoder scoring, sorting, and top-five selection.

### Current retrieval parameters

| Setting | Current value | Where it is set |
|---|---:|---|
| Chunk size | 1,000 characters | `create_chunks()` default |
| Chunk overlap | 200 characters | `create_chunks()` default |
| Embedding model | `all-MiniLM-L6-v2` | `app/services/embeddings.py` |
| Query expansion model | `qwen3:4b` | `app/services/query_expansion.py` |
| Candidates requested per expanded query | 20 | `retrieve(..., candidate_k=20)` |
| Maximum expanded query count | 5, including original question | `expand_query()` |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` | `app/services/retriever.py` |
| Chunks sent to answer generation | 5 | `retrieve(..., top_k=5)` |
| Answer generation model | `qwen3:4b` | `app/services/generator.py` |
| ChromaDB persistence path | `./storage/chroma` | `app/services/vector_store.py` |
| ChromaDB collection | `documents` | `app/services/vector_store.py` |

Chunk size and overlap are character counts, not token counts. Chunks are created separately for each extracted page, so a chunk does not span across two pages.

## Data models and structures

### SQLAlchemy tables

**`User`** (`app/models/user.py`, table `users`)

| Field | Python/SQLAlchemy declaration | Meaning in this code |
|---|---|---|
| `id` | `Mapped[int]`, primary key | User row identifier. |
| `name` | `Mapped[str]`, `String(255)` | User's name. |
| `email` | `Mapped[str]`, `String(255)`, unique | Email used as the login identifier. |
| `hashed_password` | `Mapped[str]`, `String(255)` | Password hash saved at registration. |

**`Document`** (`app/models/document.py`, table `documents`)

| Field | Python/SQLAlchemy declaration | Meaning in this code |
|---|---|---|
| `id` | `Mapped[int]`, primary key | Document row identifier; this ID is also used as the ChromaDB document ID metadata value. |
| `filename` | `Mapped[str]`, `String(255)` | Original uploaded filename. |
| `user_id` | `Mapped[int]`, foreign key to `users.id` | User row associated with the document. |

### Pydantic schemas

- `schemas.auth.Token`: `access_token: str`, `token_type: str`.
- `schemas.auth.TokenData`: `email: str | None`, defaulting to `None`.
- `schemas.auth.User`: `name: str`, optional `email`, and `password: str`; used as the registration request body.
- `schemas.auth.UserInDB`: `id: int`, `name: str`, optional `email`, and `hashed_password: str`.
- `schemas.chat.ChatRequest`: `document_ids: list[int]` and `question: str`.

### In-memory structures used by the pipeline

- **Extracted page:** a dictionary with `page` (one-based integer) and `text` (string).
- **Chunk:** a dictionary with `text` (string slice) and `page` (integer).
- **Embedding:** the list returned by `SentenceTransformer.encode(...).tolist()`, passed to ChromaDB as a vector.
- **Chroma metadata:** a dictionary containing `page`, `document_id`, and `filename`.
- **Retrieval candidate map:** `candidates` is a dictionary keyed by `(document text, JSON-serialized metadata)`. Each value contains `document` and `metadata`; this supports deduplication across expanded queries.
- **Reranking pairs:** a list of `(query, document_text)` tuples, one pair for each candidate and each expanded query.
- **API upload response:** a dictionary containing `documents`, whose entries contain `document_id`, `filename`, and `chunks`.
- **API chat response:** a dictionary containing `answer` and `sources`; each source has `filename` and `page`.

## API endpoints

| Method | Path | Input | Behavior |
|---|---|---|---|
| `GET` | `/health` | None | Returns `{"status": "ok"}`. |
| `POST` | `/auth/register` | JSON matching `schemas.auth.User` | Hashes the password, inserts a user, and returns a bearer token. |
| `POST` | `/auth/token` | OAuth2 form fields `username` and `password`; `username` is treated as email | Authenticates credentials and returns a bearer token. |
| `GET` | `/auth/users/me/` | Bearer token | Returns the current user as `UserInDB`. |
| `POST` | `/documents/upload` | Bearer token plus multipart field `files` containing one or more files | Saves, extracts, chunks, embeds, and indexes each uploaded file. |
| `GET` | `/documents/list` | Bearer token | Returns document rows belonging to the current user. |
| `POST` | `/chat/` | JSON with `document_ids: list[int]` and `question: str` | Retrieves chunks for those IDs and generates an answer with source metadata. |

FastAPI's interactive API documentation is available at `/docs` when the application is running.

### Example chat request

```json
{
  "document_ids": [1],
  "question": "What projects and technical skills are described in this document?"
}
```

The response shape is:

```json
{
  "answer": "Generated answer text",
  "sources": [
    {
      "filename": "example.pdf",
      "page": 1
    }
  ]
}
```

The answer text and source values above are illustrative response shapes, not output from a live request.

## Project layout

```text
Queriva-main/
├── app/
│   ├── main.py                   # FastAPI app, middleware, router registration, health endpoint
│   ├── ab_testing_rag.py         # Standalone full-PDF-context experiment; not imported by the API
│   ├── api/routes/
│   │   ├── auth.py               # Registration, token login, current-user endpoint
│   │   ├── documents.py          # PDF upload/indexing and document listing
│   │   └── chat.py               # Question-answering endpoint
│   ├── core/
│   │   ├── config.py             # Loads .env settings
│   │   ├── database.py           # SQLAlchemy engine and DeclarativeBase
│   │   └── security.py           # OAuth2 bearer token dependency
│   ├── models/
│   │   ├── user.py               # User SQLAlchemy model
│   │   └── document.py           # Document SQLAlchemy model
│   ├── schemas/
│   │   ├── auth.py               # Authentication Pydantic models
│   │   └── chat.py               # Chat request model
│   └── services/
│       ├── auth.py                # Password hashing, login verification, JWT, current-user lookup
│       ├── db.py                  # SQL operations for document records
│       ├── pdf.py                 # PDF page text extraction
│       ├── chunker.py             # Character-based chunking with overlap
│       ├── embeddings.py          # SentenceTransformer embeddings
│       ├── vector_store.py        # Persistent ChromaDB writes and filtered searches
│       ├── query_expansion.py     # LLM-generated alternative search queries
│       ├── retriever.py           # Retrieval, deduplication, reranking, top-k selection
│       └── generator.py           # Prompt construction and answer generation
├── alembic/
│   ├── env.py                     # Alembic runtime configuration
│   └── versions/                  # SQL schema migration scripts
├── docs/
│   └── problem-solving/
│       └── retrieval-improvements.md # Notes on the indirect-question retrieval experiment
├── alembic.ini
├── pyproject.toml
├── uv.lock
└── README.md
```

Some documentation files and package `__init__.py` files in the repository are empty. They do not currently contain additional behavior.

## Configuration

The settings class in `app/core/config.py` loads a `.env` file with `python-dotenv` and reads the following variables:

| Variable | Use |
|---|---|
| `DATABASE_URL` | SQLAlchemy database connection URL; used to create the engine and configure Alembic. |
| `SECRET_KEY` | Key used to sign and validate JWT access tokens. |
| `ALGORITHM` | JWT signing/verification algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime in minutes; defaults to `30` if unset. |
| `GEMINI_API_KEY` | Read into settings, but not used by the current PDF question-answering pipeline shown in this repository. |

Create a local `.env` file with values appropriate for your environment. Example structure:

```dotenv
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE
SECRET_KEY=replace-with-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

The database URL example is a template; replace the placeholders with your actual database details. Do not commit `.env` or real secrets.

The current code uses Ollama for query expansion and answer generation, with model name `qwen3:4b`. That model must be available to the Ollama service. The embedding and reranking models are loaded through SentenceTransformers and may need to be downloaded on first use.

## Run locally

The project declares dependencies in `pyproject.toml` and includes `uv.lock`.

1. Install Python and `uv` in your environment.
2. From the project root, install the locked dependencies:

   ```bash
   uv sync
   ```

3. Create the `.env` file described above and ensure the configured SQL database is reachable.
4. Ensure Ollama is installed and running, and that the model used by the code is available:

   ```bash
   ollama pull qwen3:4b
   ```

5. Apply the database migrations:

   ```bash
   uv run alembic upgrade head
   ```

6. Start the API from the project root:

   ```bash
   uv run uvicorn app.main:app --reload
   ```

7. Open `http://127.0.0.1:8000/docs` to inspect and call the endpoints.

These are the commands implied by the dependencies and application structure; this README does not claim that the application has been run successfully in your environment.

### CORS

`app/main.py` currently allows the origin `http://localhost:3000`, credentials, all methods, and all headers. Change this configuration if your frontend runs at a different origin.

## Database migrations

Alembic configuration is in `alembic.ini`; `alembic/env.py` imports `Base` and the `User` and `Document` models so their metadata can be used for migrations. It sets Alembic's SQLAlchemy URL from `settings.DATABASE_URL`.

The migration history contains:
1. `18cece4ff770_init_migration.py`: creates `users` and `documents`; the initial `users` schema uses a `password` column.
2. `4055f48d061e_update_users_table.py`: adds `hashed_password` and drops `password`.

The current `User` model defines `hashed_password`, matching the second migration's intended final schema.

## Implementation notes and current limitations

These notes describe behavior visible in the current code and are important when using or extending the project:

- **Chat route authentication:** unlike the document upload and list routes, `POST /chat/` does not declare a `get_current_user` dependency. The code accepts document IDs from the request and filters ChromaDB by those IDs, but it does not verify in that route that the selected documents belong to the requesting user.
- **Document IDs:** `vector_store.search()` filters on the supplied `document_ids`; ownership enforcement is not implemented there.
- **File validation:** the upload route accepts `UploadFile` objects but does not explicitly validate MIME type, file extension, PDF signature, file size, or upload limits before writing the bytes to a `.pdf` path.
- **Upload consistency:** the SQL document row is inserted before the file is saved and processed. The current route does not implement rollback/cleanup across the SQL row, saved file, and vector-store writes if a later step fails.
- **Database sessions:** `get_user()` creates a SQLAlchemy `Session` without a context manager and does not explicitly close it in that function. The document service functions do use `with Session(engine)`.
- **Registration errors:** registration checks for a missing email and password, but does not explicitly handle duplicate-email database errors in the route.
- **PDF extraction:** the extractor reads text from PDF pages. The code does not implement OCR for scanned/image-only PDFs; pages with empty extracted text are skipped.
- **Chunking:** chunking is character-based and independently applied to each page. There is no token-aware chunking.
- **Source output:** chat sources include filename and page, not chunk IDs or quoted passages. The source array is assembled from the selected retrieval metadata and is not separately deduplicated.
- **Fallback model:** `app/core/config.py` contains a comment about a future Ollama fallback, but no fallback implementation is present there.
- **Gemini setting:** `GEMINI_API_KEY` is loaded, and `google-genai` is listed as a dependency, but the current `generator.py` and `query_expansion.py` use Ollama.
- **Experiment script:** `app/ab_testing_rag.py` uses a hard-coded local PDF path (`data/uploads/2.pdf`) and is a standalone script, not an endpoint or part of the normal API call flow.
- **Imports:** some modules contain imports that are not used by their current implementation. They do not create additional features.
- **Runtime verification:** the README describes code paths and configuration; it does not assert that deployment, external services, model downloads, or every endpoint have been tested in a fresh environment.

## Retrieval experiment

`docs/problem-solving/retrieval-improvements.md` records an experiment around the question, “What job roles suit me best and why?” It contrasts sending full PDF text directly to the model with the earlier retrieval-based approach, which did not surface enough relevant context. The documented improvement was query expansion before semantic retrieval, followed by candidate aggregation/ranking and answer generation.

The standalone script `app/ab_testing_rag.py` demonstrates the full-PDF-context side of that comparison: it extracts all page text from a hard-coded PDF path and passes the entire text to `qwen3:4b`. It is not wired into `app/main.py` or the chat endpoint.
