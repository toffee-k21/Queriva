# Queriva — Commands

Commands reference for the Queriva FastAPI + PostgreSQL + Alembic + ChromaDB + Ollama project.

> Run commands from the project root (the folder containing `pyproject.toml`, `uv.lock`, and `alembic.ini`). These commands are written for macOS/Linux shells. Replace example values with your own. Never paste real passwords or API secrets into Git.

## 1. First-time setup

```bash
# Check Python and uv are installed
python3 --version
uv --version

# Install dependencies from pyproject.toml / uv.lock
uv sync

# Create/edit .env using the template in README.md
# (This repository may not include an .env.example file.)
```

Required environment variables are documented in `README.md`: `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, and optionally `ACCESS_TOKEN_EXPIRE_MINUTES`. `GEMINI_API_KEY` is currently read by settings but isn't used by the current RAG answer pipeline. Keep `.env` private; it is gitignored.

## 2. Start the backend

```bash
# Start FastAPI with automatic reload for development
uv run uvicorn app.main:app --reload
```

Useful URLs while the server is running:

- API / Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Health check: http://127.0.0.1:8000/health

Stop the development server with `Ctrl+C`.

## 3. PostgreSQL checks

Make sure PostgreSQL is running and that `DATABASE_URL` in `.env` points to the right database.

```bash
# Check whether PostgreSQL is accepting connections (default local port)
pg_isready

# Connect with psql (replace database/user with your own)
psql -U YOUR_DB_USER -d YOUR_DB_NAME

# Inside psql, useful commands
\conninfo
\dt
\d users
\d documents
\q
```

If PostgreSQL is remote or uses a non-default port, check that host/port in `DATABASE_URL` and use the corresponding options with `pg_isready`/`psql`.

## 4. Alembic migrations (important)

Run these from the project root. Alembic is configured by `alembic.ini` and `alembic/env.py`.

```bash
# See the database's current migration revision
uv run alembic current

# List migration history
uv run alembic history

# List latest migration heads
uv run alembic heads

# Generate a migration after changing SQLAlchemy models
uv run alembic revision --autogenerate -m "describe the schema change"

# Apply all pending migrations to the configured database
uv run alembic upgrade head

# Show details for a particular revision
uv run alembic show REVISION_ID

# Undo one migration (use carefully; may remove schema/data)
uv run alembic downgrade -1
```

### The usual migration workflow

1. Edit the SQLAlchemy model(s) under `app/models/`.
2. Generate a migration:
   ```bash
   uv run alembic revision --autogenerate -m "add a field to documents"
   ```
3. Open the new file in `alembic/versions/` and carefully review both `upgrade()` and `downgrade()`. Autogenerate is a draft; it can miss or misinterpret changes.
4. Apply it locally:
   ```bash
   uv run alembic upgrade head
   ```
5. Check the result:
   ```bash
   uv run alembic current
   ```
6. Commit the model and migration together:
   ```bash
   git add app/models/ alembic/versions/
   git commit -m "db: describe schema change"
   ```

**Important:** `alembic revision` creates a migration file; it does not apply it. `alembic upgrade head` applies it to the database. `git commit` records the code/migration in Git; it does not change the database. Don't delete or edit an already-shared migration casually. Avoid downgrading a database with important data until you've reviewed what the downgrade does and have a backup.

## 5. Ollama (local LLM)

Queriva currently uses the `qwen3:4b` model for query expansion and answer generation.

```bash
# Check Ollama is installed
ollama --version

# Download the model used by the project
ollama pull qwen3:4b

# List locally available models
ollama list

# Run the model interactively (Ctrl+D or /bye to exit)
ollama run qwen3:4b
```

Ollama must be running and reachable by the backend. On systems where Ollama is installed as a background service, launch/start it using the normal method for that OS. Model downloads can take time and disk space.

## 6. ChromaDB / local RAG storage

The persistent ChromaDB directory is configured in `app/services/vector_store.py`:

```text
./storage/chroma
```

It is generated application data and is gitignored. Don't delete it unless you intentionally want to reset local vector data; deleting it can remove the stored document embeddings/chunks and force re-ingestion.

```bash
# See whether the directory exists
ls -lah storage/chroma

# Inspect uploaded/generated data folders if present
find data -maxdepth 2 -type f
```

Uploaded PDFs are temporary processing inputs; follow the upload route's cleanup behavior. Don't manually remove files while an upload is being processed.

## 7. Git commands I use often

```bash
# Check modified/untracked files
git status

# Review changes before staging
git diff

# Stage selected files
git add COMMANDS.md app/models/ alembic/versions/

# Commit changes
git commit -m "docs: add project command cheat sheet"

# See recent commits
git log --oneline -10

# Pull latest changes from the current branch
git pull

# Push current branch to its configured remote
git push
```

Before committing, make sure `.env`, uploaded PDFs, and local vector database files are not staged:

```bash
git status --short
```

## 8. Handy Python / dependency commands

```bash
# Add a dependency to the project using uv (updates pyproject.toml and lockfile)
uv add PACKAGE_NAME

# Add a development-only dependency
uv add --dev PACKAGE_NAME

# Sync environment with project dependencies
uv sync

# Run a Python command inside the project environment
uv run python --version

# Check CLI help
uv run alembic --help
uv run uvicorn --help
```

## 9. Common issues

- **`alembic` / package command not found:** use `uv run ...` from the project root after `uv sync`.
- **Database connection refused:** verify PostgreSQL is running, `DATABASE_URL` is correct, and the host/port is reachable.
- **Migration says no changes detected:** verify the model is imported into the SQLAlchemy metadata used by `alembic/env.py`; inspect the database and model definitions before assuming no migration is needed.
- **Migration fails:** read the complete error, fix the migration or database state, then retry. Don't blindly delete migration files or edit Alembic's version table.
- **Ollama model not found:** run `ollama pull qwen3:4b` and verify with `ollama list`.
- **Slow first request:** SentenceTransformers embedding/reranking models may need to download/load the first time.
- **RAG results missing:** confirm the document was ingested, the expected document ID is selected, and `storage/chroma` is available.

## 10. Quick start — commands I usually need

```bash
# Terminal 1: confirm database is available
pg_isready

# Terminal 2: from the Queriva root
uv sync
uv run alembic upgrade head
ollama list
uv run uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs to test the API. Keep PostgreSQL and Ollama running in their required services/terminals.

## Official migration reference

- [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Alembic autogenerate documentation](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
