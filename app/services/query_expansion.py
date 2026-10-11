import json
from ollama import chat


def expand_query(question: str) -> list[str]:
    response = chat(
        model="qwen3:4b",
        messages=[
            {
                "role": "system",
                "content": """
                You generate search queries for a PDF retrieval system.

                Generate 3-4 concise queries that search for different
                pieces of evidence needed to answer the user's question.

                Consider relevant skills, projects, experience,
                technologies, achievements, or other document sections
                depending on the question.

                Do not answer the question.
                Return a JSON array of strings only.
                """
            },
            {
                "role": "user",
                "content": question
            }
        ],
        format="json"
    )

    try:
        queries = json.loads(response.message.content)

        # Support either a JSON array or an object containing queries.
        if isinstance(queries, dict):
            queries = queries.get("queries", [])

        if not isinstance(queries, list):
            return [question]

        queries = [
            q.strip()
            for q in queries
            if isinstance(q, str) and q.strip()
        ]

        # Keep the original question and remove duplicate queries.
        return list(dict.fromkeys([question, *queries]))[:5]

    except (json.JSONDecodeError, TypeError):
        return [question]