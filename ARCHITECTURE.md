# Architecture Overview
##  Module Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                          main.py                                │
│                    (FastAPI Endpoints)                          │
└────┬──────────────────┬──────────────────┬──────────────────────┘
     │                  │                  │
     │                  │                  │
     ▼                  ▼                  ▼
┌─────────────┐  ┌──────────────┐  ┌──────────────┐
│   config.py │  │text_processing│  │ llm_utils.py │
│(Settings)   │  │    .py        │  │(Groq Chat)   │
└─────────────┘  └──────────────┘  └──────────────┘
                                           │
                 ┌─────────────────────────┘
                 │
                 ▼
      ┌─────────────────────┐
      │document_extractor.py│
      │   (Orchestrator)    │
      └──────────┬──────────┘
                 │
       ┌─────────┼─────────┐
       │         │         │
       ▼         ▼         ▼
  ┌────────┐ ┌──────┐ ┌────────────┐
  │pdf_utils│ │ocr_  │ │unstructured│
  │  .py   │ │utils │ │_utils.py   │
  │(PyMuPDF)│ │.py   │ │(Fallback)  │
  └────────┘ └──────┘ └────────────┘
```

## Data Flow

### Upload Flow
```
User uploads file
      │
      ▼
   main.py (/upload-image)
      │
      ▼
document_extractor.extract_text_and_tables()
      │
      ├──► pdf_utils (if native PDF)
      │         │
      │         └──► extract_tables_from_pdf_fast()
      │
      ├──► ocr_utils (if scanned PDF/image)
      │         │
      │         ├──► extract_from_image_tesseract_only()
      │         └──► extract_from_image_easyocr()
      │
      └──► unstructured_utils (last resort)
                │
                └──► extract_with_unstructured() [with timeout]
      │
      ▼
text_processing.split_text_into_chunks()
      │
      ▼
Store in document_context (in-memory)
      │
      ▼
Return response to user
```

### Chat Flow
```
User sends chat message
      │
      ▼
   main.py (/chat)
      │
      ▼
llm_utils.chat_with_llm()
      │
      ├──► find_relevant_chunk() (if document loaded)
      │         │
      │         └──► text_processing.count_tokens()
      │
      ├──► build_system_message() (with context)
      │
      └──► Groq API call
      │
      ▼
Return LLM response to user
```

### 3. **Layered Architecture**
```
Presentation Layer:  main.py (FastAPI)
                        │
Business Logic:     document_extractor, llm_utils
                        │
Utility Layer:      pdf_utils, ocr_utils, text_processing
                        │
Infrastructure:     PyMuPDF, Tesseract, Groq API
```

##  Memoria

| Component | Memoria    |
|-----------|------------|
| FastAPI base | ~50MB      |
| PyMuPDF | ~20MB      |
| Tesseract | ~10MB      |
| EasyOCR (if loaded) | ~500MB     |
| Unstructured | ~200MB     |
| LangChain | ~30MB      |
| **Total (without EasyOCR)** | **~310MB** |
| **Total (with EasyOCR)** | **~810MB** |
