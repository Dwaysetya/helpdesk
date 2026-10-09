from datetime import datetime
import logging
import requests
import config
import os
import platform
import threading

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

def check_and_play_alarm(data: dict):
    """
    Checks the report data for 0 hits, N/A rates, or Errors, and plays a loud alarm if found.
    """
    alert = False
    for cat, metrics in data.items():
        hits = metrics.get('total_hits')
        if hits is not None and (hits == '0' or hits == 'N/A' or 'Error' in hits):
            alert = True
        total_id = metrics.get('total_id')
        if total_id is not None and (total_id == '0' or total_id == 'N/A' or 'Error' in total_id):
            alert = True
        rate = metrics.get('success_rate')
        if rate is not None and (rate == 'N/A' or 'Error' in rate):
            alert = True
            
    if alert:
        logger.warning("🚨 Anomaly detected (0 hits or N/A)! Triggering loud audio alarm...")
        def alarm_task():
            if platform.system() == "Darwin":
                # Set Mac volume to 100%
                os.system("osascript -e 'set volume output volume 100'")
                # Speak loudly and play a sound repeatedly
                for _ in range(5):
                    os.system('say "Wake up! Wake up! There is an issue with the Kibana report! Check the dashboard immediately!"')
                    os.system('afplay /System/Library/Sounds/Glass.aiff')
                    os.system('afplay /System/Library/Sounds/Ping.aiff')
            else:
                import time
                for _ in range(10):
                    print('\\a')
                    time.sleep(1)
                    
        # Run in a background thread so it doesn't block the message sending
        threading.Thread(target=alarm_task, daemon=True).start()

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

def send_whatsapp_message(text: str, photo_path: str = None) -> bool:
    """
    Sends a message to WhatsApp using a local/self-hosted HTTP API Gateway.
    Now supports sending images if photo_path is provided.
    """
    if not config.WHATSAPP_API_URL or not config.WHATSAPP_RECIPIENT_PHONE:
        logger.warning("WhatsApp API URL or Recipient Phone is not configured. Skipping WhatsApp notification.")
        return False

    headers = {
        "Content-Type": "application/json"
    }
    
    if config.WHATSAPP_API_TOKEN:
        headers["apikey"] = config.WHATSAPP_API_TOKEN
        headers["Authorization"] = f"Bearer {config.WHATSAPP_API_TOKEN}"

    if photo_path and os.path.exists(photo_path):
        import base64
        try:
            with open(photo_path, "rb") as f:
                encoded_image = base64.b64encode(f.read()).decode("utf-8")
            
            # Auto-adapt Evolution API endpoint from sendText to sendMedia
            api_url = config.WHATSAPP_API_URL.replace("/sendText", "/sendMedia")
            
            payload = {
                "number": config.WHATSAPP_RECIPIENT_PHONE,
                "to": config.WHATSAPP_RECIPIENT_PHONE,
                "phone": config.WHATSAPP_RECIPIENT_PHONE,
                "mediatype": "image",
                "mimetype": "image/png",
                "caption": text,
                "media": encoded_image
            }
        except Exception as e:
            logger.error(f"Failed to read image for WhatsApp: {e}")
            return False
    else:
        api_url = config.WHATSAPP_API_URL
        payload = {
            "number": config.WHATSAPP_RECIPIENT_PHONE,
            "to": config.WHATSAPP_RECIPIENT_PHONE,
            "phone": config.WHATSAPP_RECIPIENT_PHONE,
            "text": text,
            "message": text
        }

    try:
        logger.info(f"Sending message to WhatsApp API Gateway: {api_url}")
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code in [200, 201]:
            logger.info("WhatsApp message sent successfully.")
            return True
        else:
            logger.error(f"WhatsApp API Gateway returned status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {str(e)}")
        return False
