import warnings
from typing import Tuple, List, Optional
from PIL import Image, ImageEnhance
import pytesseract
import numpy as np
import cv2

# Esconder os avisos do PyTorch sobre pin_memory quando nenhuma GPU está disponível.
warnings.filterwarnings('ignore', message='.*pin_memory.*')

from config import (
    EASYOCR_LANGUAGES, 
    EASYOCR_GPU, 
    TESSERACT_DEFAULT_LANG, 
    TESSERACT_FALLBACK_LANG,
    TABLE_COLUMN_VARIATION_TOLERANCE
)

_easyocr_reader = None

def get_easyocr_reader():
    global _easyocr_reader
    
    if _easyocr_reader is None:
        print("Carregando EasyOCR (primeira vez)...")
        try:
            import easyocr
            _easyocr_reader = easyocr.Reader(EASYOCR_LANGUAGES, gpu=EASYOCR_GPU)
            print("EasyOCR carregado!")
        except Exception as e:
            print(f" Erro ao carregar EasyOCR: {e}")
            print(" Usando apenas Tesseract como fallback")
            _easyocr_reader = "DISABLED"
    
    return _easyocr_reader if _easyocr_reader != "DISABLED" else None

def enhance_image_quality(image: Image.Image) -> Image.Image:

    width, height = image.size
    min_dimension = min(width, height)

    target_size = 2000
    if min_dimension < target_size:
        scale_factor = target_size / min_dimension
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)

        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        print(f" Imagem redimensionada de {width}x{height} para {new_width}x{new_height}")

    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)

    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2.0)

    return image

def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    img_array = np.array(image)

    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array

    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )
    denoised = cv2.fastNlMeansDenoising(thresh, h=20)

    return Image.fromarray(denoised)


def extract_from_image_tesseract_only(image: Image.Image) -> Tuple[str, List[str]]:

    try:
        pytesseract.get_tesseract_version()
    except Exception as e:
        error_msg = (
            "Tesseract OCR não está instalado. "
            "Instale com: sudo apt install tesseract-ocr tesseract-ocr-por"
        )
        print(f" {error_msg}")
        raise RuntimeError(error_msg) from e

    enhanced_image = enhance_image_quality(image)
    preprocessed_image = preprocess_image_for_ocr(enhanced_image)

    try:
        ocr_data = pytesseract.image_to_data(
            preprocessed_image,
            lang=TESSERACT_DEFAULT_LANG,
            output_type=pytesseract.Output.DATAFRAME,
            config='--psm 3'
        )
    except Exception as e:

        try:
            ocr_data = pytesseract.image_to_data(
                preprocessed_image,
                lang=TESSERACT_FALLBACK_LANG,
                output_type=pytesseract.Output.DATAFRAME,
                config='--psm 3'
            )
        except Exception as fallback_error:
            print(f"Erro no Tesseract: {fallback_error}")
            raise

    try:
        text_simple = pytesseract.image_to_string(preprocessed_image, lang=TESSERACT_DEFAULT_LANG)
    except:
        text_simple = pytesseract.image_to_string(preprocessed_image, lang=TESSERACT_FALLBACK_LANG)

    tables = []

    if not ocr_data.empty:
        # Filter out null text entries
        ocr_data = ocr_data[ocr_data['text'].notnull()].copy()

        if not ocr_data.empty and len(ocr_data) > 0:
            # Group words by line (top position) - 20px tolerance
            ocr_data['line_num'] = (ocr_data['top'] // 20)

            grouped = ocr_data.groupby('line_num')
            table_rows = []

            for _, group in grouped:
                # Sort words left to right
                row_words = group.sort_values('left')['text'].tolist()

                # Lines with multiple words could be table rows
                if len(row_words) >= 2:
                    table_rows.append(row_words)

            if len(table_rows) > 2:
                col_counts = [len(row) for row in table_rows]
                variation = max(col_counts) - min(col_counts)

                if variation <= TABLE_COLUMN_VARIATION_TOLERANCE:
                    for row in table_rows:
                        md_row = "| " + " | ".join([str(w) for w in row]) + " |"
                        tables.append(md_row)

    return text_simple.strip(), tables


def extract_from_image_easyocr(image: Image.Image) -> Tuple[str, List[str]]:

    reader = get_easyocr_reader()

    if reader is None:
        # EasyOCR not available, use Tesseract
        return extract_from_image_tesseract_only(image)

    try:
        # Enhance image quality before processing
        enhanced_image = enhance_image_quality(image)

        result = reader.readtext(np.array(enhanced_image), detail=1)
        text_easyocr = " ".join([txt for bbox, txt, conf in result if conf > 0.3])

        if len(text_easyocr.strip()) < 50:
            print("⚠EasyOCR encontrou pouco texto, tentando Tesseract também...")
            text_tesseract, tables = extract_from_image_tesseract_only(image)
            

            if len(text_tesseract) > len(text_easyocr):
                print("esseract encontrou mais texto, usando resultado do Tesseract")
                return text_tesseract, tables
            else:
                _, tables = extract_from_image_tesseract_only(image)
                return text_easyocr.strip(), tables
        else:
            _, tables = extract_from_image_tesseract_only(image)
            return text_easyocr.strip(), tables

    except Exception as e:
        print(f"Erro no EasyOCR: {e}, usando Tesseract")
        return extract_from_image_tesseract_only(image)
