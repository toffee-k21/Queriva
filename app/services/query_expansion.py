
import json
import logging

from app.services.llm import generate_text

logger = logging.getLogger(__name__)


def expand_query(question: str) -> list[str]:
    system_prompt = """
    You generate search queries for a PDF retrieval system.

    Generate 3-4 concise queries that search for different
    pieces of evidence needed to answer the user's question.

    Consider relevant skills, projects, experience,
    technologies, achievements, or other document sections
    depending on the question.

    Do not answer the question.
    Return a JSON array of strings only.
    """.strip()

    try:
        response = generate_text(
            system_prompt=system_prompt,
            user_prompt=question,
            json_mode=True,
        )

        queries = json.loads(response)

        # Support a JSON array or an object containing queries.
        if isinstance(queries, dict):
            queries = queries.get("queries", [])

        if not isinstance(queries, list):
            return [question]

        queries = [
            q.strip()
            for q in queries
            if isinstance(q, str) and q.strip()
        ]

        # Keep the original question and remove duplicates.
        return list(dict.fromkeys([question, *queries]))[:5]

    except Exception:
        logger.exception(
            "Query expansion failed; using the original question."
        )
        return [question]
