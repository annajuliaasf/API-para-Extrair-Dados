from typing import Dict, List
from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, LLM_MAX_TOKENS
from text_processing import count_tokens

client = Groq(api_key=GROQ_API_KEY)

def find_relevant_chunk(chunks: List[str], prompt: str) -> tuple:

    if len(chunks) <= 1:
        return chunks[0] if chunks else "", ""

    query_words = [w.lower() for w in prompt.split() if len(w) > 3]
    scores = []

    for chunk in chunks:
        score = sum(chunk.lower().count(word) for word in query_words)
        scores.append(score)

    best_idx = scores.index(max(scores)) if scores else 0
    relevant_text = chunks[best_idx]
    context_note = f"\n[Documento com {len(chunks)} partes. Exibindo seção mais relevante.]"
    
    return relevant_text, context_note

def build_system_message(
    relevant_text: str, 
    filename: str, 
    extraction_method: str,
    tables: List[str],
    context_note: str = ""
) -> str:

    tables_str = ""
    if tables:
        tables_str = "\n\nTABELAS DETECTADAS:\n" + "\n".join(tables[:10])
    
    system_message = f"""Você é um assistente que responde perguntas sobre documentos.
        DOCUMENTO: {filename}{context_note}
        MÉTODO: {extraction_method}

        CONTEÚDO: {relevant_text}
        {tables_str}

        Analise o documento fornecido e responda apenas com base nas informações presentes no arquivo. Para tabelas,
        use os dados estruturados fornecidos. Caso não seja possível identificar a resposta correta, informe que não
        sabe, mas mencione que se o cliente enviar um documento mais legível, como fatura, recibo ou documento 
        pessoal, será possível responder. Se houver palavras incompletas, por exemplo “M4ria”, tente inferir a letra
        mais provável no lugar do número ou caractere identificado; neste caso, o “4” provavelmente seria a letra A.
        Para retornar CPF ou outros documentos oficiais, garanta que o dado esteja no formato correto, 
        como xxx.xxx.xxx-xx. Priorize sempre a precisão e não invente informações que não estejam presentes no 
        documento."""


    return system_message

def chat_with_llm(
    prompt: str, 
    document_context: Dict = None
) -> Dict:

    messages = []
    has_context = False
    context_file = None
    chunks_available = 0
    extraction_method = "N/A"

    if document_context and "last_document" in document_context:
        has_context = True
        context_file = document_context.get('last_filename')
        chunks_available = document_context.get('num_chunks', 1)
        extraction_method = document_context.get('extraction_method', 'N/A')

        if "chunks" in document_context and len(document_context["chunks"]) > 1:
            relevant_text, context_note = find_relevant_chunk(
                document_context["chunks"], 
                prompt
            )
        else:
            relevant_text = document_context["last_document"]
            context_note = ""

        if count_tokens(relevant_text) > 4000:
            relevant_text = relevant_text[:16000]  # ~4000 tokens

        system_message = build_system_message(
            relevant_text,
            document_context.get('last_filename', 'Desconhecido'),
            extraction_method,
            document_context.get('tables', []),
            context_note
        )
        
        messages.append({"role": "system", "content": system_message})

    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        max_tokens=LLM_MAX_TOKENS
    )

    return {
        "response": response.choices[0].message.content,
        "Existe contexto": has_context,
        "Contexto": context_file,
        "Chunks": chunks_available,
        "Metodo de extraçao": extraction_method
    }
