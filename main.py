from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import time

from document_extractor import extract_text_and_tables
from text_processing import count_tokens, split_text_into_chunks
from llm_utils import chat_with_llm

CORS_ORIGINS = ["*"]
CORS_CREDENTIALS = True
CORS_METHODS = ["*"]
CORS_HEADERS = ["*"]

app = FastAPI(
    title="Leitor de documentos e extrator de informações",
    description="Optimized document extraction and chat API",
    version="3.0.0"
)

document_context: Dict[str, Any] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_CREDENTIALS,
    allow_methods=CORS_METHODS,
    allow_headers=CORS_HEADERS,
)

@app.post("/upload-documento")
async def upload_image(file: UploadFile = File(...)) -> Dict:
    # Validate file type
    if not file.content_type:
        raise HTTPException(status_code=400, detail="Tipo de arquivo não identificado")

    allowed_types = ["image/jpeg", "image/jpg", "image/png", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Formato não suportado. Use: JPEG, JPG, PNG ou PDF"
        )

    try:
        # Read file and determine type
        file_bytes = await file.read()
        file_type = "pdf" if file.content_type == "application/pdf" else "image"

        start_time = time.time()
        result = extract_text_and_tables(
            file_bytes=file_bytes,
            file_type=file_type,
            filename=file.filename
        )
        elapsed_time = time.time() - start_time

        if not result["text"].strip():
            raise HTTPException(status_code=400, detail="Não foi possível extrair texto")

        text = result["text"]
        tables = result.get("tables", [])
        method = result.get("method", "Unknown")

        tokens = count_tokens(text)
        chunks = split_text_into_chunks(text) if tokens > 4000 else [text]

        document_context["last_document"] = text
        document_context["last_filename"] = file.filename
        document_context["chunks"] = chunks
        document_context["total_tokens"] = tokens
        document_context["num_chunks"] = len(chunks)
        document_context["tables"] = tables
        document_context["extraction_method"] = method

        return {
            "success": True,
            "filename": file.filename,
            "file_type": file.content_type,
            "extraction_method": method,
            "text": text,
            "tables": tables,
            "total_tokens": tokens,
            "total_characters": len(text),
            "chunks": len(chunks),
            "tables_count": len(tables),
            "time_taken": round(elapsed_time, 2),
            "message": f"Documento processado com {method}"
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/chat")
def chat(prompt: str, use_context: bool = True):
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt não pode estar vazio")

    try:
        context = document_context if use_context else None
        result = chat_with_llm(prompt, context)
        return result
    except Exception as e:
        if "413" in str(e) or "rate_limit" in str(e):
            return {
                "response": "Documento muito grande.",
                "error": "Limite de tokens"
            }
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")


# ======= CONTEXT MANAGEMENT =======
@app.post("/clear-context")
def clear_context():
    document_context.clear()
    return {"message": "Contexto limpo com sucesso!"}


@app.get("/context-info")
def context_info():
    if "last_document" in document_context:
        return {
            "has_context": True,
            "filename": document_context.get('last_filename'),
            "text_length": len(document_context['last_document']),
            "total_tokens": document_context.get('total_tokens', 0),
            "num_chunks": document_context.get('num_chunks', 1),
            "tables_detected": len(document_context.get('tables', [])),
            "extraction_method": document_context.get('extraction_method', 'Unknown'),
            "preview": document_context['last_document'][:500] + "..."
        }
    return {"has_context": False, "message": "Nenhum documento carregado"}

@app.get("/")
def root():
    return {
        "name": "PDF OCR API - Raw Extraction",
        "version": "3.0.0",
        "description": "Extract raw text from PDFs and images",
        "endpoints": {
            "/upload-documento": "POST - Upload and extract text",
            "/chat": "POST - Chat with extracted context",
            "/clear-context": "POST - Clear document context",
            "/context-info": "GET - Info about current context",
            "/docs": "GET - API documentation"
        },
        "supported_formats": ["PDF", "JPEG", "JPG", "PNG"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
