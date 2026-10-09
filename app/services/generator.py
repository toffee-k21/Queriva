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

    Answer the user's question using the provided PDF context.

    - If the answer is directly stated in the context, answer from it.
    - If the question asks for an opinion, advice, suggestion, summary, or
    recommendation, reason from the information in the context and give a
    well-supported answer based on it.
    - Do not invent facts that are not supported by the context.
    - Only say "I could not find enough information in the PDF to answer
    this question." if the context contains nothing relevant to the question.

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