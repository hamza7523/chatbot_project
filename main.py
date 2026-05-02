from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.connection import db
from services.gemini_service import ask_gemini
from pydantic import BaseModel
import traceback

app = FastAPI(title="Freelance Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Existing model for UI
class ChatRequest(BaseModel):
    prompt_id: int

# NEW: Model for AWS Lambda (File-based processing)
class ExternalChatRequest(BaseModel):
    prompt_text: str

@app.get("/health")
def health_check():
    return { "status": "ok" }

# 1. NEW ENDPOINT FOR ASSIGNMENT #2 (S3 + Lambda)
@app.post("/api/external/chat")
async def external_chat(request: ExternalChatRequest):
    try:
        # This bypasses MongoDB and sends the S3 file content directly to Gemini
        print(f"📥 Received prompt from S3 file via Lambda: {request.prompt_text[:50]}...")
        reply = await ask_gemini(request.prompt_text)
        return { "reply": reply }
    except Exception as e:
        print("ERROR:", str(e))
        return { "reply": f"Error: {str(e)}" }

# 2. EXISTING ENDPOINT (For UI/MongoDB flow)
@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        prompt_doc = await db.prompts.find_one({"id": request.prompt_id}, {"_id": 0})
        if not prompt_doc:
            return { "reply": "Invalid ID." }
        reply = await ask_gemini(prompt_doc["system_prompt"])
        return { "reply": reply }
    except Exception as e:
        return { "reply": f"Error: {str(e)}" }
