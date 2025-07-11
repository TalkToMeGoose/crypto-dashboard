import os
import requests
from typing import Optional

def send_telegram_message(text: str) -> bool:
    """Send message to Telegram chat"""
    token = os.getenv('TG_TOKEN')
    chat_id = os.getenv('TG_CHAT')
    
    if not token or not chat_id:
        print(f"Telegram alert (no bot configured): {text}")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    try:
        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown"
            },
            timeout=10
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")
        return False