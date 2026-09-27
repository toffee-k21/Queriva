from ollama import chat


def generate_answer(
    question,
    documents,
    metadatas
):
    context_parts = []

    for text, metadata in zip(documents, metadatas):
        context_parts.append(
            f"--- Page {metadata['page']} ---\n"
            f"{text}"
        )

    context = "\n\n".join(context_parts)

    prompt = f"""
You are a helpful PDF question-answering assistant.

Answer the user's question using ONLY the provided PDF context.

If the answer cannot be found in the context, say:

"I could not find enough information in the PDF to answer this question."

Do not make up information.

PDF CONTEXT:
{context}

USER QUESTION:
{question}
"""

    response = chat(
        model="qwen3:4b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.message.content