import fitz


def extract_pdf(pdf_path: str):

    doc = fitz.open(pdf_path)

    pages = []

    for page_number, page in enumerate(doc):

        text = page.get_text().strip()

        if text:

            pages.append({
                "page": page_number + 1,
                "text": text
            })

    doc.close()

    return pages