import fitz
from ..models.document import DocumentMetaData, Document, PageDocument


def read_pdf(path: str, metadata: DocumentMetaData = None):
    doc = fitz.open(path)

    pages = []
    for i in range(len(doc)):
        page = doc[i]

        page_document = PageDocument(content=page.get_text("text"), page_number=i + 1)
        pages.append(page_document)

    document = Document(pages=pages, metadata=metadata)
    return document
