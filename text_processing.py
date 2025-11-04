from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import CHUNK_SIZE, CHUNK_OVERLAP, TOKEN_ESTIMATION_RATIO

def count_tokens(text: str) -> int:
    return len(text) // TOKEN_ESTIMATION_RATIO

def split_text_into_chunks(
    text: str, 
    chunk_size: int = CHUNK_SIZE, 
    chunk_overlap: int = CHUNK_OVERLAP
) -> List[str]:

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        add_start_index=True
    )
    chunks = splitter.split_text(text)
    return chunks
