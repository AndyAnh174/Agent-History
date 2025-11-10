from __future__ import annotations

from langchain.text_splitter import RecursiveCharacterTextSplitter


def split_text(
    text: str,
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> list[str]:
    """Split raw text into overlapping chunks suited for embedding."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)
