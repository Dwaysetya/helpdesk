import asyncio
import os
from telethon import TelegramClient
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    phone = os.getenv("TELEGRAM_PHONE_NUMBER")
    
    if not api_id or not api_hash or not phone or api_id == "your_api_id_here":
        print("Error: TELEGRAM_API_ID, TELEGRAM_API_HASH, atau TELEGRAM_PHONE_NUMBER belum diisi dengan benar di .env")
        print("Silakan isi terlebih dahulu sebelum menjalankan script ini.")
        return

    print(f"Mencoba login untuk nomor: {phone}")
    print("Mengecek file sesi 'userbot.session'...")
    
    # Create the client and connect
    client = TelegramClient('userbot', api_id, api_hash)
    
    async def login():
        await client.start(phone=phone)
        me = await client.get_me()
        print(f"\nSukses! Berhasil login sebagai: {me.first_name} (@{me.username})")
        print("File 'userbot.session' telah berhasil dibuat di folder ini.")
        print("Sekarang Anda bisa menjalankan 'python main.py' dan pesan akan terkirim dari akun Anda!")
        
    with client:
        client.loop.run_until_complete(login())

if __name__ == '__main__':
    main()
