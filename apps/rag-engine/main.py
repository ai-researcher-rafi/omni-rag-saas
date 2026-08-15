import os
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

# LangChain & PDF Processing Libraries
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb

load_dotenv()

# Gemini AI Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ChromaDB Persistent Client (Vector Storage)
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "./chroma_data")
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

app = FastAPI(
    title="omni-rag-saas PDF Processing & RAG Engine",
    description="Multi-Tenant Vector Storage with PDF Chunking and Gemini AI Routing",
    version="1.1.0"
)

# Request Schema
class QueryRequest(BaseModel):
    tenant_id: str
    prompt: str

@app.get("/")
def health_check():
    return {"status": "online", "engine": "Python RAG Engine v1.1"}

# ==========================================
# 1. PDF Upload & Text Chunking API Route
# ==========================================
@app.post("/api/v1/rag/upload")
async def upload_and_chunk_pdf(
    tenant_id: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        # Step A: Temporary File Save
        temp_dir = "./temp_files"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Step B: Read PDF Content
        reader = PdfReader(file_path)
        extracted_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"

        # Cleanup temporary file
        os.remove(file_path)

        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="No readable text found in PDF.")

        # Step C: Text Chunking (1000 characters per chunk, 200 overlap)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_text(extracted_text)

        # Step D: Save Chunks in Tenant-Isolated ChromaDB Collection
        collection = chroma_client.get_or_create_collection(name=f"tenant_{tenant_id}")
        
        documents = []
        metadatas = []
        ids = []

        for index, chunk in enumerate(chunks):
            documents.append(chunk)
            metadatas.append({"tenant_id": tenant_id, "chunk_index": index, "file_name": file.filename})
            ids.append(f"{tenant_id}_doc_{index}_{file.filename}")

        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        return {
            "success": True,
            "message": "PDF successfully processed, chunked, and vectorized!",
            "tenant_id": tenant_id,
            "filename": file.filename,
            "total_chunks_created": len(chunks)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 2. Vector Context Search & RAG Query Route
# ==========================================
@app.post("/api/v1/rag/query")
async def process_rag_query(request: QueryRequest):
    try:
        if not GEMINI_API_KEY:
            raise HTTPException(status_code=500, detail="Gemini API Key missing.")

        # Step A: Search Context from ChromaDB
        context_text = ""
        try:
            collection = chroma_client.get_collection(name=f"tenant_{request.tenant_id}")
            results = collection.query(
                query_texts=[request.prompt],
                n_results=3  # Top 3 most relevant chunks
            )
            if results and 'documents' in results and results['documents']:
                context_text = "\n".join(results['documents'][0])
        except Exception:
            context_text = "No stored document context found for this tenant."

        # Step B: Build Prompt with Context
        final_prompt = f"""
        You are an AI assistant for Tenant: {request.tenant_id}.
        Answer the question strictly based on the provided document context below:
        
        [DOCUMENT CONTEXT]
        {context_text}
        
        [USER QUESTION]
        {request.prompt}
        """

        # Step C: Primary Model Execution with Fail-Safe Fallback
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(final_prompt)
            return {
                "success": True,
                "tenant_id": request.tenant_id,
                "response": response.text,
                "model_used": "gemini-1.5-flash (Primary)",
                "context_found": bool(context_text)
            }
        except Exception as primary_error:
            # Fail-Safe Pipeline (Fallback)
            print(f"[Fail-Safe Triggered]: {primary_error}")
            fallback_model = genai.GenerativeModel('gemini-1.5-pro')
            fallback_response = fallback_model.generate_content(final_prompt)
            return {
                "success": True,
                "tenant_id": request.tenant_id,
                "response": fallback_response.text,
                "model_used": "gemini-1.5-pro (Fail-Safe Fallback)",
                "context_found": bool(context_text)
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))