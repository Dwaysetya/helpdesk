import asyncio
import os
from telethon import TelegramClient
from dotenv import load_dotenv

async def main():
    load_dotenv()
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    
    client = TelegramClient('userbot', api_id, api_hash)
    await client.connect()
    
    async for dialog in client.iter_dialogs():
        print(f"Chat: {dialog.name}, ID: {dialog.id}")
        
    await client.disconnect()

asyncio.run(main())
