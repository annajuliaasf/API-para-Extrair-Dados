from typing import Dict, Optional
import os
import tempfile
import signal
from langchain_community.document_loaders import UnstructuredFileLoader
from config import (
    UNSTRUCTURED_TIMEOUT, 
    UNSTRUCTURED_MODE, 
    UNSTRUCTURED_STRATEGY
)

def extract_with_unstructured(
    file_bytes: bytes, 
    filename: str, 
    file_type: str, 
    timeout: int = UNSTRUCTURED_TIMEOUT
) -> Optional[Dict]:

    def timeout_handler(signum, frame):
        raise TimeoutError("O Unstructured demorou demais para responder")

    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"upload_{os.getpid()}_{filename}")

    try:
        # Save file temporarily
        with open(temp_path, "wb") as f:
            f.write(file_bytes)

        print(f" Tentando Unstructured em: {filename} (timeout: {timeout}s)")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)

        loader_kwargs = {
            "mode": UNSTRUCTURED_MODE,
            "estratégia": UNSTRUCTURED_STRATEGY,
        }

        loader = UnstructuredFileLoader(temp_path, **loader_kwargs)
        docs = loader.load()

        signal.alarm(0)

        if not docs:
            print("Unstructured não retornou documentos")
            return None

        text_parts = []
        tables_found = []

        for doc in docs:
            content = doc.page_content.strip()
            if content:
                if '|' in content or '\t' in content:
                    tables_found.append(content)
                text_parts.append(content)

        full_text = "\n\n".join(text_parts)

        print(f" Unstructured: {len(full_text)} chars, {len(tables_found)} tabelas")

        return {
            "text": full_text,
            "tables": tables_found,
            "method": "Unstructured"
        }

    except TimeoutError:
        print(f"️ Unstructured timeout após {timeout}s")
        return None
    except Exception as e:
        print(f" Erro no Unstructured: {type(e).__name__}: {str(e)}")
        return None

    finally:
        try:
            signal.alarm(0)
        except:
            pass
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
