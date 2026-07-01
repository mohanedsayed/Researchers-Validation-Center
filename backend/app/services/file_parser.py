import os
from pathlib import Path

import docx

def parse_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def parse_md(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def parse_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)

def parse_file(file_path: str, file_format: str) -> str:
    if file_format == "txt":
        return parse_txt(file_path)
    elif file_format == "md":
        return parse_md(file_path)
    elif file_format == "docx":
        return parse_docx(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_format}")
