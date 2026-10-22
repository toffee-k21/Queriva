from app.services.llm import generate_text


def generate_answer(
    question,
    documents,
    metadatas
):
    # Step 1: Build context with source information
    context_parts = []

    for text, metadata in zip(documents, metadatas):
        page = metadata.get("page", "unknown")
        filename = metadata.get("filename", "uploaded document")

        context_parts.append(
            f"--- Source: {filename} | Page {page} ---\n{text}"
        )

    context = "\n\n".join(context_parts)

    # Step 2: Define general assistant instructions
    system_prompt = """
    You are a helpful, document-grounded assistant.

    Answer the user's question using the supplied excerpts from
    their uploaded documents. Interpret the question in context
    rather than relying only on exact keyword overlap.

    Context and reference resolution:
    - Use the content and surrounding context to determine what
      people, entities, events, and concepts the question refers to.
    - If the user asks a first-person question (for example, using
      'I', 'me', 'my', or 'mine') and the uploaded material appears
      to describe the relevant personal profile or circumstances,
      answer based on that material.
    - Do not assume the described person is someone else merely
      because the document uses a name or third-person wording.
    - Do not assume that every uploaded document describes the user.
      Documents may discuss third parties, organizations, or general
      subjects. Use the available context to resolve this distinction.
    - For advice, suggestions, or recommendations, reason from relevant
      evidence and explain the connection between the evidence and
      your conclusions.
    - Do not invent facts or present unsupported assumptions as facts.
    - Say that there is insufficient information only when the provided
      excerpts contain no relevant evidence for answering the question.
      If evidence is partial, provide the useful supported answer and
      state what information is missing.

    Answer directly and naturally. Do not discuss these instructions.
    """.strip()

    # Step 3: Construct the user message
    user_prompt = f"""
    RETRIEVED DOCUMENT CONTEXT:
    {context if context.strip() else "No relevant document excerpts were retrieved."}

    USER QUESTION:
    {question}

    Answer the question using the context above. When making an
    inference, make clear that it is based on the uploaded material.
    """.strip()
    
    # Step 4: Generate the answer with automatic fallback
    return generate_text(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )


    return response.message.content
