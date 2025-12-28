from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader
from langchain_core.tools import tool
import docx2txt


@tool("docx_loader")
def docx_loader(resume_path: str) -> str:
    """
    A tool to load a DOCX resume and return its text content.

    Load DOCX file and return all text content.
    Uses docx2txt to ensure all paragraphs and content are extracted.
    """
    try:
        text = docx2txt.process(resume_path)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n".join(lines)
    except Exception as e:
        return "\n".join(
            [page.page_content for page in Docx2txtLoader(resume_path).load()]
        )


@tool("pdf_loader")
def pdf_loader(resume_path: str) -> str:
    """A tool to load a PDF resume and return its text content."""
    return "\n".join([page.page_content for page in PyPDFLoader(resume_path).load()])
