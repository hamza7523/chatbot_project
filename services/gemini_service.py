import google.generativeai as genai
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

async def ask_gemini(system_prompt: str) -> str:
    # run_in_executor lets a sync function run without blocking async code
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, model.generate_content, system_prompt)
    return response.text