from datetime import datetime
import logging
import requests
import config
import os

logger = logging.getLogger("KibanaScraper.Notifier")

def format_report_message(data: dict) -> str:
    """
    Formats the scraped data exactly according to the user's group reporting template:
    - Adds current local time (e.g., 15.00)
    - Puts a single divider line under the header
    - Bolds the "Total Hits" and "Total Homepass ID" metric values using asterisks
    """
    assurance_data = data.get("assurance", {})
    surrounding_data = data.get("surrounding", {})
    homepass_data = data.get("homepass", {})
    reservasi_data = data.get("reservasi_homepass", {})

    # Formats current time based on configuration (e.g. 15.00 or 15.28)
    time_str = datetime.now().strftime(config.REPORT_TIME_FORMAT)

    message = f"""Pantauan seluruh transaksi DIMAS dari Elastic {time_str}
———————————————————
📍 Assurance
Total Hits: **{assurance_data.get('total_hits', 'N/A')}**
Success Rate : {assurance_data.get('success_rate', 'N/A')}

📍 Surrounding
Total Hits: **{surrounding_data.get('total_hits', 'N/A')}**
Success Rate : {surrounding_data.get('success_rate', 'N/A')}

📍 Homepass
Total Hits: **{homepass_data.get('total_hits', 'N/A')}**
Success Rate : {homepass_data.get('success_rate', 'N/A')}

📍 Reservasi Homepass
Total Homepass ID: **{reservasi_data.get('total_id', 'N/A')}**
success reserve : {reservasi_data.get('success_rate', 'N/A')}"""

    return message

async def send_telegram_message(text: str, photo_path: str = None) -> bool:
    """
    Sends a message to the configured Telegram chat using Telethon (Userbot).
    """
    if not config.TELEGRAM_API_ID or not config.TELEGRAM_API_HASH or not config.TELEGRAM_CHAT_ID:
        logger.warning("Telegram API ID, API Hash, or Chat ID is not configured. Skipping Telegram notification.")
        return False

    try:
        from telethon import TelegramClient
        # Telethon uses integer for chat ID if it's a group ID, but can also parse string if it's a username/link.
        # We try to convert to int if it looks like one (e.g. -3816123180)
        try:
            chat_id = int(config.TELEGRAM_CHAT_ID)
        except ValueError:
            chat_id = config.TELEGRAM_CHAT_ID
            
        client = TelegramClient('userbot', config.TELEGRAM_API_ID, config.TELEGRAM_API_HASH)
        
        # Connect to Telegram without prompting for phone (relies on existing userbot.session)
        await client.connect()
        if not await client.is_user_authorized():
            logger.error("Userbot is not authorized! Please run 'python telegram_login.py' first.")
            return False
            
        if photo_path and os.path.exists(photo_path):
            logger.info("Sending photo message via Telegram Userbot...")
            await client.send_file(chat_id, photo_path, caption=text, parse_mode='md')
        else:
            logger.info("Sending text message via Telegram Userbot...")
            await client.send_message(chat_id, text, parse_mode='md')
            
        logger.info("Telegram message sent successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram message via Userbot: {str(e)}")
        return False
    finally:
        if 'client' in locals() and client:
            try:
                await client.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting client: {str(e)}")

def send_whatsapp_message(text: str) -> bool:
    """
    Sends a message to WhatsApp using a local/self-hosted HTTP API Gateway.
    
    Common self-hosted WhatsApp API Gateways and their payloads:
    1. Evolution API (Recommended):
       - Endpoint: POST http://localhost:8080/message/sendText/<instance_name>
       - Headers: {"apikey": "<token>", "Content-Type": "application/json"}
       - Body: {"number": "628123456789", "text": "...", "delay": 1200}
       
    2. wwebjs-api / Baileys custom HTTP endpoints:
       - Endpoint: POST http://localhost:8080/send
       - Body: {"to": "628123456789@c.us", "message": "..."}
    """
    if not config.WHATSAPP_API_URL or not config.WHATSAPP_RECIPIENT_PHONE:
        logger.warning("WhatsApp API URL or Recipient Phone is not configured. Skipping WhatsApp notification.")
        return False

    headers = {
        "Content-Type": "application/json"
    }
    
    # Add authorization token header if configured
    if config.WHATSAPP_API_TOKEN:
        # Standard header formats (e.g. Apikey, Authorization Bearer, etc.)
        # Modify this according to your specific API Gateway requirements.
        headers["apikey"] = config.WHATSAPP_API_TOKEN
        headers["Authorization"] = f"Bearer {config.WHATSAPP_API_TOKEN}"

    # Build payload dynamically. This is a generic layout.
    # Adjust target payload structure depending on your WhatsApp API Gateway (e.g. 'number', 'to', 'chatId').
    payload = {
        "number": config.WHATSAPP_RECIPIENT_PHONE,  # Common format for Evolution API
        "to": config.WHATSAPP_RECIPIENT_PHONE,      # Common format for wwebjs/Baileys
        "phone": config.WHATSAPP_RECIPIENT_PHONE,   # Alternative common format
        "text": text,                               # Message body key
        "message": text                             # Alternative message body key
    }

    try:
        logger.info(f"Sending message to WhatsApp API Gateway: {config.WHATSAPP_API_URL}")
        response = requests.post(config.WHATSAPP_API_URL, json=payload, headers=headers, timeout=20)
        
        # Verify success criteria. Most APIs return 200 or 201 on success.
        if response.status_code in [200, 201]:
            logger.info("WhatsApp message sent successfully.")
            return True
        else:
            logger.error(f"WhatsApp API Gateway returned status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {str(e)}")
        return False
