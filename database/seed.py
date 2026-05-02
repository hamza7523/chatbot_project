import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

async def seed():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    db = client[os.getenv("DATABASE_NAME")]

    prompts = [
        {
            "id": 1,
            "option_label": "Get project info",
            "system_prompt": "You are a helpful assistant for a freelance business. Provide information about services: logo design ($50), website development ($300), branding packages ($150). Be friendly and concise.",
            "category": "info"
        },
        {
            "id": 2,
            "option_label": "Place an order",
            "system_prompt": "You are an order assistant. Help the user place an order. Ask for: their name, email, service they want, and project details. Confirm the order at the end.",
            "category": "order"
        },
        {
            "id": 3,
            "option_label": "Check order status",
            "system_prompt": "You are a status assistant. Ask the user for their email or order ID and tell them their order is being processed. Be reassuring and professional.",
            "category": "status"
        }
    ]

    # Insert all prompts into the "prompts" collection
    await db.prompts.insert_many(prompts)
    print(" Database seeded successfully!")

asyncio.run(seed())