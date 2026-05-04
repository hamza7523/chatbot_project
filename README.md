# BriefAI — Serverless Freelance Proposal Generator

> A learning project built to understand **serverless compute architecture** and **AWS Lambda event-driven pipelines**. The AI layer uses Google Gemini, but the model is intentionally abstracted — it can be swapped for any company's fine-tuned LLM without touching the infrastructure.

---

## Overview

BriefAI lets a freelancer upload a plain-text client brief through a web UI. The file triggers a serverless pipeline that analyzes the brief and returns a structured proposal — with deliverables, timeline, and pricing — in under 30 seconds.

The core goal was not to build a chatbot. It was to understand **how S3 event triggers, Lambda execution, and async backend communication work together** as a serverless pattern — and why this matters for production ML systems.

![BriefAI Landing Page](./ui-hero.png)

<img width="1859" height="880" alt="image" src="https://github.com/user-attachments/assets/3ac07bb7-2a21-42a4-ae8a-4773179697d3" />

---

## Architecture

```
Client Browser
     │
     │  PUT .txt file
     ▼
Amazon S3 (input bucket)
     │
     │  S3 Event Notification (ObjectCreated)
     ▼
AWS Lambda (Python 3.14)
     │
     │  HTTP POST  { "prompt_text": "..." }
     ▼
FastAPI Backend (EC2)
     │
     │  Gemini API call
     ▼
Google Gemini 2.5 Flash
     │
     │  Generated proposal text
     ▼
Amazon S3 (output bucket)
     │
     │  UI polls → reads response
     ▼
Client Browser (displays proposal)
```

**Why this architecture?** S3 → Lambda → API is a common event-driven pattern in production ML systems — used for batch inference, document processing pipelines, and async prediction jobs. Understanding how to wire these pieces together was the main learning objective.

---

## What I Learned

- How S3 event notifications trigger Lambda functions on file upload
- How Lambda reads from one S3 bucket and writes results to another
- The difference between synchronous API calls and async event-driven processing
- How to structure a FastAPI backend to accept payloads from serverless functions
- Why decoupling the compute layer (Lambda) from the model layer (Gemini/any LLM) matters for maintainability

---

## Model Abstraction

The current implementation uses **Google Gemini 2.5 Flash** via the `google-generativeai` SDK. The model call is isolated in `services/gemini_service.py` and is the only place in the codebase that knows which model is being used.

This means the Gemini call can be replaced with:
- A company's **fine-tuned LLM** hosted on a custom endpoint
- An **OpenAI-compatible API** (Azure OpenAI, Together AI, etc.)
- A **locally hosted model** via Ollama or vLLM on the same EC2 instance
- An **Amazon Bedrock** model for a fully AWS-native stack

The Lambda function, S3 trigger, and FastAPI routing stay completely unchanged. Only `services/gemini_service.py` needs to be updated.

---

## Screenshots

### S3 Buckets — Input and Output

Two buckets: one receives the uploaded brief, one stores the generated proposal after Lambda writes it back.

![S3 Buckets](./s3-buckets.png)

<img width="1052" height="481" alt="image" src="https://github.com/user-attachments/assets/28124ca6-5435-44c4-be15-fbaaf7b96931" />


### Lambda Execution Logs (CloudWatch)

End-to-end trace showing the S3 trigger firing, the EC2 backend being called, and the response being saved — total duration ~18 seconds including Gemini generation time.

![Lambda CloudWatch Logs](./lambda-logs.png)
<img width="1528" height="640" alt="image" src="https://github.com/user-attachments/assets/797e0081-47b6-4a06-a1dd-313e0de39b24" />

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vanilla HTML/CSS/JS — single file, no framework |
| File storage | AWS S3 (input + output buckets) |
| Serverless compute | AWS Lambda (Python 3.14, triggered by S3 events) |
| Backend | FastAPI on EC2 (ap-southeast-2) |
| LLM | Google Gemini 2.5 Flash (swappable) |
| Database | MongoDB Atlas via Motor (async) |
| Config | python-dotenv |

---

## Project Structure

```
briefai/
├── main.py                   # FastAPI app — two endpoints
├── services/
│   └── gemini_service.py     # LLM abstraction layer (swap model here)
├── database/
│   ├── connection.py         # MongoDB async client
│   └── seed.py               # Seed prompt templates
├── lambda/
│   └── handler.py            # Lambda function — S3 trigger → EC2 → S3
├── frontend/
│   └── index.html            # Single-page UI
├── requirements.txt
└── .env.example
```

---

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Fill in MONGODB_URL, GEMINI_API_KEY, DATABASE_NAME

# Start the server
uvicorn main:app --reload --port 8000
```

**Endpoints:**

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/chat` | Fetch prompt from MongoDB by ID and send to Gemini |
| `POST` | `/api/external/chat` | Accept raw prompt text — used by Lambda |

---

## Lambda Setup

The Lambda function (`lambda/handler.py`) is configured with:
- **Trigger:** S3 `ObjectCreated` event on the input bucket
- **Runtime:** Python 3.14
- **Timeout:** 60 seconds (Gemini generation can take 15–20s)
- **Memory:** 512 MB
- **Output:** Writes `response_to_{filename}.txt` to the output bucket

> **Note:** The Lambda reads the FastAPI response using `response_data.get('reply')` — make sure this matches the key returned by your backend.

---
---

## File Structure

```
briefai/
│
├── main.py                        # FastAPI entry point
│                                  # Two endpoints:
│                                  #   POST /api/chat          → MongoDB prompt by ID → Gemini
│                                  #   POST /api/external/chat → raw prompt text → Gemini (used by Lambda)
│
├── services/
│   ├── __init__.py
│   ├── gemini_service.py          # Only file that talks to Gemini
│   │                              # Swap this file to change the model
│   └── prompt_service.py          # (extendable) prompt management helpers
│
├── database/
│   ├── __init__.py
│   ├── connection.py              # Async MongoDB client via Motor
│   └── seed.py                    # Seeds prompt templates into MongoDB
│                                  # Run once: python database/seed.py
│
├── models/
│   ├── prompt.py                  # Pydantic schemas for prompts
│   └── order.py                   # Pydantic schemas for orders
│
├── lambda/
│   └── handler.py                 # AWS Lambda function
│                                  # Triggered by S3 ObjectCreated event
│                                  # Reads brief → calls FastAPI → writes response to output bucket
│
├── frontend/
│   └── index.html                 # Single-file UI — no framework, no build step
│                                  # Uploads .txt to S3 directly using AWS SDK
│                                  # Polls output bucket for the generated proposal
│
├── test_db.py                     # Quick script to verify MongoDB connection
├── requirements.txt
├── .env                           # Never commit this
└── .env.example                   # Commit this instead
```

---

## Self-Hosting Setup

This project has three independent pieces you need to set up: the FastAPI backend on EC2, the Lambda function on AWS, and the frontend locally. Follow the steps in order.

### Prerequisites

- Python 3.10+
- An AWS account with programmatic access (Access Key + Secret Key)
- A MongoDB Atlas account (free tier works)
- A Google AI Studio account for the Gemini API key

---

### Step 1 — Clone and configure environment

```bash
git clone https://github.com/your-username/briefai.git
cd briefai

pip install -r requirements.txt

cp .env.example .env
```

Open `.env` and fill in your values:

```env
MONGODB_URL=mongodb+srv://<user>:<password>@cluster0.xxxx.mongodb.net/?appName=Cluster0
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_NAME=freelance_db
```

Get your Gemini key at [aistudio.google.com](https://aistudio.google.com). MongoDB URL comes from your Atlas cluster's **Connect → Drivers** page.

---

### Step 2 — Seed the database

This inserts the default prompt templates into MongoDB. Only needs to run once.

```bash
python database/seed.py
```

Verify it worked:

```bash
python test_db.py
# Expected output:
# ✅ Connected! Collections: ['prompts']
# 📄 Prompts in DB: 3
```

---

### Step 3 — Run the FastAPI backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Test it is running:

```bash
curl http://localhost:8000/health
# { "status": "ok" }
```

For production, run this on an EC2 instance. Make sure port 8000 is open in your EC2 security group inbound rules (Custom TCP, port 8000, source 0.0.0.0/0).

---

### Step 4 — Create S3 buckets

Go to AWS S3 and create two buckets in the same region:

| Bucket | Purpose |
|---|---|
| `ai-prompts-input-<yourname>` | Receives uploaded brief files from the UI |
| `ai-responses-output-<yourname>` | Stores generated proposals written by Lambda |

On each bucket, go to **Permissions → CORS** and paste this — required for the browser to upload directly:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST"],
    "AllowedOrigins": ["*"],
    "ExposeHeaders": []
  }
]
```

---

### Step 5 — Deploy the Lambda function

1. Go to **AWS Lambda → Create function**
2. Choose **Author from scratch**, Runtime: **Python 3.12**
3. Paste the contents of `lambda/handler.py` into the inline editor
4. Update these two lines at the top of the file to match your setup:

```python
BACKEND_URL = "http://<your-ec2-public-ip>:8000/api/external/chat"
OUTPUT_BUCKET = "ai-responses-output-<yourname>"
```

5. Under **Configuration → General**, set timeout to **60 seconds** and memory to **512 MB**

6. Under **Configuration → Permissions**, attach a policy to the Lambda execution role that allows `s3:GetObject` on the input bucket and `s3:PutObject` on the output bucket:

```json
{
  "Effect": "Allow",
  "Action": ["s3:GetObject"],
  "Resource": "arn:aws:s3:::ai-prompts-input-<yourname>/*"
},
{
  "Effect": "Allow",
  "Action": ["s3:PutObject"],
  "Resource": "arn:aws:s3:::ai-responses-output-<yourname>/*"
}
```

7. Add the S3 trigger: **+ Add trigger → S3 → select input bucket → Event type: PUT**

> **Important:** In `lambda/handler.py` line 27, make sure you read `response_data.get('reply')` not `response_data.get('response')` — `reply` is what the FastAPI endpoint returns.

---

### Step 6 — Open the frontend

No build step needed. Just open `frontend/index.html` directly in your browser.

Click **Connection settings** and fill in:

| Field | Value |
|---|---|
| AWS Access Key | Your IAM user access key |
| AWS Secret Key | Your IAM user secret key |
| Input Bucket | `ai-prompts-input-<yourname>` |
| Output Bucket | `ai-responses-output-<yourname>` |
| Region | Your bucket region e.g. `ap-southeast-2` |

Upload a `.txt` file containing a client brief and hit **Generate proposal**. The UI will upload to S3, wait for Lambda to process it, poll the output bucket, and display the result when ready.

---

### Common Issues

**Upload fails with CORS error** — Make sure you added the CORS policy to your S3 input bucket in Step 4.

**Lambda times out** — Gemini can take 15–20 seconds. Ensure Lambda timeout is set to at least 60 seconds.

**No response in output bucket** — Check CloudWatch logs for your Lambda function. The most likely cause is either the EC2 backend is not running or port 8000 is blocked in your security group.

**`reply` is empty** — Confirm your Lambda reads `response_data.get('reply')` and not `response_data.get('response')`.

## Next Steps

- [ ] Add MLflow experiment tracking to log prompt versions and response quality metrics
- [ ] Expose a `/metrics` endpoint on FastAPI for Prometheus scraping
- [ ] Build a Grafana dashboard showing proposal generation volume, Gemini latency, and Lambda duration over time
- [ ] Add a pre-signed URL endpoint on FastAPI so the frontend doesn't need direct AWS credentials

---

## Author

**Hamza** — Final year BS Computer Science, IBA Karachi (2026)  
Focus: ML Infrastructure · MLOps · AI Engineering
