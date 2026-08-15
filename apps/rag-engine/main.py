import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Gemini AI Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI(
    title="omni-rag-saas Core RAG Engine",
    description="Vector Retrieval & Gemini AI Engine with Multi-Tenant Support",
    version="1.0.0"
)

class QueryRequest(BaseModel):
    tenant_id: str
    prompt: str

@app.get("/")
def health_check():
    return {
        "status": "online",
        "engine": "Python RAG Engine",
        "version": "1.0.0"
    }

# Mocking Vector RAG Search & Fail-Safe Routing
@app.post("/api/v1/rag/query")
async def process_rag_query(request: QueryRequest):
    try:
        if not GEMINI_API_KEY:
            raise HTTPException(status_code=500, detail="Gemini API Key missing")

        # Primary Model Pipeline (Gemini 1.5 Flash)
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            context_prompt = f"[Tenant: {request.tenant_id}] User asked: {request.prompt}"
            response = model.generate_content(context_prompt)
            return {
                "success": True,
                "tenant_id": request.tenant_id,
                "response": response.text,
                "model_used": "gemini-1.5-flash (Primary)"
            }
        except Exception as primary_error:
            # Fail-Safe Pipeline (Fallback Model Routing)
            print(f"[Fail-Safe Triggered]: Primary model failed: {primary_error}")
            fallback_model = genai.GenerativeModel('gemini-1.5-pro')
            fallback_response = fallback_model.generate_content(request.prompt)
            return {
                "success": True,
                "tenant_id": request.tenant_id,
                "response": fallback_response.text,
                "model_used": "gemini-1.5-pro (Fail-Safe Fallback)"
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))