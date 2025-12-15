from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader
from langchain_core.tools import tool
import docx2txt

@tool("docx_loader", description="A tool to load a DOCX resume and return its text content")
def docx_loader(resume_path: str) -> str:
    """
    Load DOCX file and return all text content.
    Uses docx2txt to ensure all paragraphs and content are extracted.
    """
    try:
        # Use docx2txt directly to ensure all content is extracted
        text = docx2txt.process(resume_path)
        # Clean up extra whitespace but preserve line breaks
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)
    except Exception as e:
        # Fallback to langchain loader if docx2txt fails
        return "\n".join([page.page_content for page in Docx2txtLoader(resume_path).load()])

@tool("pdf_loader", description="A tool to load a PDF resume and return its text content.")
def pdf_loader(resume_path: str) -> str:
    return "\n".join([page.page_content for page in PyPDFLoader(resume_path).load()])




