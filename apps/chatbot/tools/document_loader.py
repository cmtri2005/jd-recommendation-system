from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader
from langchain_core.tools import tool

@tool("docx_loader", description="A tool to load a DOCX resume and return its text content")
def docx_loader(resume_path: str) -> str:
    return "\n".join([page.page_content for page in Docx2txtLoader(resume_path).load()])

@tool("pdf_loader", description="A tool to load a PDF resume and return its text content.")
def pdf_loader(resume_path: str) -> str:
    return "\n".join([page.page_content for page in PyPDFLoader(resume_path).load()])




