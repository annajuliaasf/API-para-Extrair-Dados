# 🧠 Proof of Concept — Sistema de Leitura e Extração de Dados de Documentos

## 📄 Descrição do Projeto

Este projeto tem como objetivo **demonstrar a viabilidade de um sistema automatizado de leitura e extração de dados de documentos**, combinando **Large Language Models (LLMs)** com outras ferramentas auxiliares de **processamento de imagem** e **reconhecimento óptico de caracteres (OCR)**.

O sistema foi desenvolvido para interpretar **documentos complexos** e obter **informações estruturadas** a partir de arquivos nos formatos **JPG, JPEG e PDF**.

---

## 🎯 Objetivos

- Comprovar a viabilidade técnica da integração entre **LLMs**, **OCR**, **pré-processamento de imagem** e **técnicas de chunking**.  
- Criar um pipeline capaz de **extrair dados estruturados** de documentos não estruturados.  
- Implementar uma **API funcional** para testes e consultas via chatbot.  

---

## 🧩 Arquitetura e Componentes

### 🧠 Large Language Model (LLM)

- **Modelo estudado:** `Llama 3.2-1B`  
- **Modelo utilizado:** `Llama 3.3-70B-Versatile` (via **Groq**)  
  - Escolhido por ser o mais próximo disponível do modelo proposto e otimizado para execução em nuvem.  
- Função: receber o texto processado e **responder perguntas de forma contextualizada** sobre o conteúdo extraído.

---

### 🔤 Reconhecimento Óptico de Caracteres (OCR)

Foram utilizados **dois mecanismos de OCR** para leitura dos documentos:

1. **Tesseract OCR**  
   - Inicialmente testado, porém apresentou **baixa eficiência** nos documentos fornecidos.  
2. **EasyOCR**  
   - Apesar de mais pesado, demonstrou **melhor acurácia** na identificação de caracteres.  

---

### 🖼️ Pré-processamento de Imagem

Antes da leitura por OCR, foi utilizado o **OpenCV** para:

- **Reduzir ruídos**  
- **Melhorar contraste**  
- **Aumentar legibilidade** do documento  

Essas etapas aumentam significativamente a precisão do OCR, especialmente em imagens com qualidade irregular.

---

### 📚 Processamento de PDFs

Para lidar com **documentos em PDF** e **preservar o layout de tabelas**, foi utilizada a biblioteca **PyMuPDF**, que permite extrair texto mantendo a estrutura visual — ao contrário de OCRs tradicionais.

---

### 🧱 Chunking

Foi implementado um processo de **divisão de texto (chunking)** para controlar o número de tokens enviados à LLM.  
Essa etapa é essencial para:

- Evitar **estouro de limite de tokens**;  
- **Preservar o contexto** entre diferentes partes do documento;  
- Otimizar custo e desempenho da inferência.

---

### 🦜🔗 Biblioteca Unstructured (LangChain)

Como último recurso, foi integrada a biblioteca **Unstructured** (LangChain), utilizada quando as outras etapas de extração falham.  

Essa biblioteca permite:

- Ler documentos em diversos formatos (PDF, DOCX, HTML, imagens etc.);  
- Dividir o conteúdo em blocos semânticos (tabelas, parágrafos, listas);  
- Estruturar dados para posterior análise por LLMs.  

---

### ⚙️ API — FASTAPI

Foi desenvolvida uma **API REST** utilizando o framework **FastAPI**, responsável por:

- Receber documentos para processamento;  
- Encaminhar o fluxo entre OCR → pré-processamento → LLM;  
- Servir o chatbot que responde perguntas sobre os documentos processados.  

---
### Acurácia

A acurácia do projeto não foi de 100%, uma vez que são determinantes fatores como qualidade da imagem e rotação. Porém, em testes com documentos nítidos, o sistema apresentou um bom funcionamento. 

### 💬 Chatbot Inteligente

O sistema inclui um **chatbot** conectado à LLM, que permite **consultas contextuais** sobre os documentos já extraídos.  
Exemplo:  
> “Qual o nome, CPF e filiação existentes na CNH”  
> “Qual o valor da conta de luz?”

--- 
 ## Link do Vídeo do Processo em Funcionamento 
 Em razão das limitações de hardware do ambiente testado, o carregamento de cada documento demorou em cerca de um minuto, por isso, o tempo de espera foi acelerado. 
[Assista ao vídeo de demonstração no YouTube]([https://www.youtube.com/watch?v=ID_DO_VIDEO](https://youtu.be/W-7hs-4x6-w))

