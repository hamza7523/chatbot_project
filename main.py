from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.connection import db
from services.gemini_service import ask_gemini
from pydantic import BaseModel
import traceback
import boto3
from botocore.config import Config

# --- CONFIGURATION ---
# These should match your AWS setup exactly
INPUT_BUCKET = "ai-briefs-input-hamza7523"
OUTPUT_BUCKET = "ai-responses-output-hamza7523"
REGION = "ap-southeast-2" 

app = FastAPI(title="Freelance Chat API")

# Enable CORS so your frontend can talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize S3 Client 
# (This will automatically use the IAM Role attached to your EC2)
s3_client = boto3.client(
    's3', 
    region_name=REGION,
    config=Config(signature_version='s3v4')
)

# --- MODELS ---

class ChatRequest(BaseModel):
    prompt_id: int

class ExternalChatRequest(BaseModel):
    prompt_text: str

# --- ENDPOINTS ---

@app.get("/health")
def health_check():
    return { "status": "ok" }

# 1. NEW: Generate Pre-signed URL for UPLOADING to S3
@app.get("/api/generate-upload-url")
async def get_upload_url(filename: str):
    try:
        # Generate a temporary link for the frontend to PUT a file into S3
        url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': INPUT_BUCKET, 
                'Key': filename, 
                'ContentType': 'text/plain'
            },
            ExpiresIn=300 # URL valid for 5 minutes
        )
        return {"url": url}
    except Exception as e:
        print(f"Error generating upload URL: {e}")
        return {"error": str(e)}

# 2. NEW: Generate Pre-signed URL for DOWNLOADING the result from S3
@app.get("/api/generate-download-url")
async def get_download_url(filename: str):
    # The Lambda function names the output as 'response_to_filename'
    response_key = f"response_to_{filename}"
    try:
        # Generate a temporary link for the frontend to GET the result file
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': OUTPUT_BUCKET, 
                'Key': response_key
            },
            ExpiresIn=300
        )
        return {"url": url}
    except Exception as e:
        print(f"Error generating download URL: {e}")
        return {"error": str(e)}

# 3. LAMBDA ENDPOINT: Receives text from Lambda, calls Gemini
@app.post("/api/external/chat")
async def external_chat(request: ExternalChatRequest):
    try:
        print(f"📥 Received prompt from S3 file via Lambda: {request.prompt_text[:50]}...")
        reply = await ask_gemini(request.prompt_text)
        return { "reply": reply }
    except Exception as e:
        print("ERROR IN EXTERNAL CHAT:", str(e))
        traceback.print_exc()
        return { "reply": f"Error: {str(e)}" }

# 4. EXISTING ENDPOINT: For UI/MongoDB flow
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
