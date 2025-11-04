from typing import Dict, Tuple
import io
import fitz  # PyMuPDF
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed

from pdf_utils import (
    check_pdf_has_native_text,
    extract_text_from_pdf_native,
    extract_tables_from_pdf_fast
)
from ocr_utils import extract_from_image_easyocr
from unstructured_utils import extract_with_unstructured
from config import OCR_DPI, OCR_PARAREL_PREPROCESSING, OCR_MAX_WORKERS

def extract_text_and_tables(file_bytes: bytes, file_type: str = "pdf", filename: str = "tempfile") -> Dict:

    # ===== Metodo 1 - tenta texto nativo com PyMuPDF
    if file_type == "pdf":
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")

        # Check if PDF has native text
        if check_pdf_has_native_text(pdf_document):
            print("PDF com texto nativo - usando PyMuPDF")

            full_text = extract_text_from_pdf_native(pdf_document)

            tables = extract_tables_from_pdf_fast(pdf_document)

            pdf_document.close()

            print(f"PyMuPDF: {len(full_text)} chars, {len(tables)} tabelas")

            return {
                "text": full_text,
                "tables": tables,
                "method": "PyMuPDF (Nativo + Rápido)"
            }

        pdf_document.close()
        print("PDF sem texto nativo - tentando OCR...")

    # ===== Metodo 2 - OCR
    tables = []
    full_text = ""

    if file_type == "pdf":
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
        page_count = pdf_document.page_count

        # Decide on parallel processing based on page count and settings
        use_parallel = OCR_PARAREL_PREPROCESSING and page_count > 1

        if use_parallel:
            print(f" Processamento paralelo: {page_count} páginas com {OCR_MAX_WORKERS} workers")

            def process_page(page_num: int) -> Tuple[int, str, list]:
                page = pdf_document[page_num]
                pix = page.get_pixmap(dpi=OCR_DPI)
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                page_text, page_tables = extract_from_image_easyocr(image)
                return page_num, page_text, page_tables

            results = []
            with ThreadPoolExecutor(max_workers=OCR_MAX_WORKERS) as executor:
                future_to_page = {
                    executor.submit(process_page, i): i
                    for i in range(page_count)
                }

                for future in as_completed(future_to_page):
                    try:
                        page_num, page_text, page_tables = future.result()
                        results.append((page_num, page_text, page_tables))
                        print(f"   ✓ Página {page_num + 1}/{page_count} processada")
                    except Exception as e:
                        page_num = future_to_page[future]
                        print(f"   ✗ Erro na página {page_num + 1}: {e}")
                        results.append((page_num, "", []))

            results.sort(key=lambda x: x[0])
            for page_num, page_text, page_tables in results:
                full_text += f"\n--- Página {page_num + 1} (OCR) ---\n{page_text}"
                tables.extend(page_tables)
        else:
            print(f" Processamento sequencial: {page_count} página(s)")
            for page_num in range(page_count):
                page = pdf_document[page_num]

                pix = page.get_pixmap(dpi=OCR_DPI)
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))

                page_text, page_tables = extract_from_image_easyocr(image)

                full_text += f"\n--- Página {page_num + 1} (OCR) ---\n{page_text}"
                tables.extend(page_tables)
                print(f" Página {page_num + 1}/{page_count} processada")

        pdf_document.close()

        if len(full_text.strip()) > 100:
            print(f"  OCR: {len(full_text)} chars, {len(tables)} tabelas")
            return {
                "text": full_text,
                "tables": tables,
                "method": "OCR (Tesseract/EasyOCR)"
            }

    else:
        image = Image.open(io.BytesIO(file_bytes))
        full_text, tables = extract_from_image_easyocr(image)

        if len(full_text.strip()) > 50:
            print(f" OCR (Imagem): {len(full_text)} chars, {len(tables)} tabelas")
            return {
                "text": full_text,
                "tables": tables,
                "method": "OCR (Tesseract/EasyOCR - Imagem)"
            }

    # ===== Metodo 3 - Unstructured (caso o OCR falhe)
    print(" OCR não foi suficiente - tentando Unstructured (pode demorar)...")
    result = extract_with_unstructured(file_bytes, filename, file_type)
    if result and result["text"].strip():
        return result

    return {
        "text": full_text if full_text.strip() else "Não foi possível extrair texto",
        "tables": tables,
        "method": "Fallback (OCR parcial)"
    }
