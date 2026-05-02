import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

async def test():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    db = client[os.getenv("DATABASE_NAME")]
    
    # Try to list all collections
    collections = await db.list_collection_names()
    print("✅ Connected! Collections:", collections)

    # Try to count prompts
    count = await db.prompts.count_documents({})
    print("📄 Prompts in DB:", count)

asyncio.run(test())