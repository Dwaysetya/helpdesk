import asyncio
import os
from telethon import TelegramClient
from dotenv import load_dotenv

async def main():
    load_dotenv()
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    chat_id = int(os.getenv("TELEGRAM_CHAT_ID"))
    
    client = TelegramClient('userbot', api_id, api_hash)
    await client.connect()
    
    try:
        entity = await client.get_entity(chat_id)
        print(f"Resolved entity: {entity}")
        await client.send_message(entity, "Test message dari Userbot!")
        print("Success!")
    except Exception as e:
        print(f"Error resolving entity or sending: {e}")
        
    await client.disconnect()

asyncio.run(main())
