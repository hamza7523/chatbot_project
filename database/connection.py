from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()  # Reads .env file and loads variables into environment

# This is the client — your app's connection to MongoDB
client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))

# Point to your specific database
db = client[os.getenv("DATABASE_NAME")]