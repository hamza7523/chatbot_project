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

class ChatRequest(BaseModel):
    prompt_id: int

@app.get("/health")
def health_check():
    return { "status": "ok" }

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        # Step 1 — query database
        print(f" Looking for prompt_id: {request.prompt_id}")
        prompt_doc = await db.prompts.find_one({"id": request.prompt_id}, {"_id": 0})
        print(f" Prompt found: {prompt_doc}")

        if not prompt_doc:
            return { "reply": "Invalid option. Please enter 1, 2, or 3." }

        # Step 2 — send to Gemini
        print(" Sending to Gemini...")
        reply = await ask_gemini(prompt_doc["system_prompt"])
        print(f" Gemini replied: {reply[:50]}")

        return { "reply": reply }

    except Exception as e:
        # Print the FULL error to terminal
        print(" ERROR:", str(e))
        traceback.print_exc()
        return { "reply": f"Error: {str(e)}" }