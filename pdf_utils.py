from typing import List, Dict, Optional
import fitz  # PyMuPDF
from config import (
    TABLE_MIN_COLUMNS, 
    TABLE_Y_POSITION_TOLERANCE, 
    TABLE_X_POSITION_BUCKET
)

def extract_tables_from_pdf_fast(pdf_document) -> List[str]:

    tables = []
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        
        try:
            blocks = page.get_text("dict")["blocks"]

            lines_dict = {}
            for block in blocks:
                if "lines" not in block:
                    continue
                    
                for line in block["lines"]:
                    y = round(line["bbox"][1] / TABLE_Y_POSITION_TOLERANCE) * TABLE_Y_POSITION_TOLERANCE
                    if y not in lines_dict:
                        lines_dict[y] = []

                    for span in line["spans"]:
                        text = span["text"].strip()
                        x = span["bbox"][0]
                        if text:
                            lines_dict[y].append((x, text))

            for y in sorted(lines_dict.keys()):
                items = sorted(lines_dict[y], key=lambda x: x[0])

                if len(items) >= TABLE_MIN_COLUMNS:
                    x_positions = [item[0] for item in items]
                    texts = [item[1] for item in items]

                    unique_columns = len(set([round(x/TABLE_X_POSITION_BUCKET)*TABLE_X_POSITION_BUCKET for x in x_positions]))
                    
                    if unique_columns >= TABLE_MIN_COLUMNS:
                        md_row = "| " + " | ".join(texts) + " |"
                        tables.append(md_row)
        
        except Exception as e:
            print(f"Erro ao detectar tabelas na página {page_num + 1}: {e}")
            continue
    
    return tables

def check_pdf_has_native_text(pdf_document, max_pages_to_check: int = 3) -> bool:

    for page_num in range(min(pdf_document.page_count, max_pages_to_check)):
        text = pdf_document[page_num].get_text("text")
        if len(text.strip()) > 50:  # Has reasonable amount of text
            return True
    return False

def extract_text_from_pdf_native(pdf_document) -> str:

    full_text = ""
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        text = page.get_text("text")
        full_text += f"\n--- Página {page_num + 1} ---\n{text}"
    return full_text
