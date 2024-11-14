import requests

def send_telegram_message(token, chat_id, message):
    """ Mengirim pesan ke Telegram menggunakan bot """
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error mengirim pesan Telegram: {e}")
