
import fitz
from ollama import chat

PDF_PATH = "data/uploads/2.pdf"
MODEL = "qwen3:4b"

question = "what job roles suit me best and why?"

prompt = """
You are a helpful PDF question-answering assistant.

Answer the user's question using the provided PDF context.

- If the answer is directly stated in the context, answer from it.
- If the question asks for an opinion, advice, suggestion, summary, or
  recommendation, reason from the information in the context and give a
  well-supported answer based on it.
- Do not invent facts that are not supported by the context.
- Only say "I could not find enough information in the PDF to answer
  this question." if the context contains nothing relevant to the question.
"""


# Extract the FULL resume text directly from the PDF
with fitz.open(PDF_PATH) as pdf:
    full_text = "\n".join(
        f"Page {i + 1}:\n{page.get_text()}"
        for i, page in enumerate(pdf)
    )

print("Resume characters:", len(full_text))


# Test A: Send the entire resume directly to the LLM
response = chat(
    model=MODEL,
    messages=[
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": (
                f"PDF CONTEXT:\n{full_text}\n\n"
                f"QUESTION:\n{question}"
            ),
        },
    ],
)

print("\n--- FULL RESUME TEST ---\n")
print(response.message.content)
