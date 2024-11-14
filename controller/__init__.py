import configparser
import requests


def read_config_topics(file_path):
    """Membaca dan mengonversi topik dan saluran dari config.ini ke dalam dictionary."""
    config = configparser.ConfigParser()
    config.read(file_path)
    
    config_topics = {}
    for section in config.sections():
        if 'nsq_address' not in config[section]:  # Abaikan nsq_address
            config_topics[section] = {}
            for key, value in config.items(section):
                if key != "nsq_address":
                    channels = [ch.strip() for ch in value.split(',')]
                    config_topics[section][key] = channels
    return config_topics

def get_nsq_data(nsq_address, check_client_count=False):
    """Mengambil data dari NSQ untuk mendapatkan topik dan channel."""
    try:
        response = requests.get(nsq_address)
        response.raise_for_status()
        nsq_data = response.json()
        
        if 'data' in nsq_data:  
            topics = nsq_data['data'].get('topics', [])
        else:
            topics = nsq_data.get('topics', [])
        
        nsq_topics = {}
        for topic in topics:
            topic_name = topic['topic_name']
            channels = topic.get('channels', [])
            channel_info = []
            
            for channel in channels:
                if check_client_count:
                    client_count = channel.get('client_count', 0)
                    channel_info.append({
                        'channel_name': channel['channel_name'],
                        'client_count': client_count
                    })
                    print(f"[INFO] Topik '{topic_name}', Channel '{channel['channel_name']}': client_count = {client_count}")
                    
                    if client_count == 0:
                        alert_message = f"[ALERT] Topik '{topic_name}', Channel '{channel['channel_name']}' memiliki client_count = 0!"
                        print(alert_message)
                        send_telegram_alert(alert_message)
                else:
                    channel_info.append({
                        'channel_name': channel['channel_name']
                    })
            
            nsq_topics[topic_name] = channel_info
        return nsq_topics
    
    except requests.exceptions.RequestException as e:
        error_message = f"Terjadi kesalahan saat menghubungi {nsq_address}: {e}"
        print(error_message)
        send_telegram_alert(error_message)
        return None

def compare_sets(config_set, nsq_set, section, nsq_name):
    """Memeriksa apakah ada perbedaan antara set saluran dan memberikan alert."""
    missing_in_nsq = config_set - nsq_set
    extra_in_nsq = nsq_set - config_set

    if missing_in_nsq:
        alert_message = f"[ALERT] Di {nsq_name}, channel '{missing_in_nsq}' hilang dari topik '{section}'"
        print(alert_message)
        send_telegram_alert(alert_message)
    if extra_in_nsq:
        alert_message = f"[ALERT] Di {nsq_name}, ada channel ekstra '{extra_in_nsq}' dalam topik '{section}'"
        print(alert_message)
        send_telegram_alert(alert_message)

def verify_topics_and_channels(config_topics, nsq_data, nsq_name, check_client_count=False):
    """Memverifikasi kesesuaian topik dan saluran antara config.ini dan data NSQ."""
    all_matched = True

    for topic, channels in config_topics.get(nsq_name, {}).items():
        if topic not in nsq_data:
            alert_message = f"[ALERT] Topik '{topic}' tidak ditemukan di {nsq_name}."
            print(alert_message)
            send_telegram_alert(alert_message)
            all_matched = False
        else:
            nsq_channels = set([ch['channel_name'] for ch in nsq_data[topic]])
            config_channels = set(channels)
            compare_sets(config_channels, nsq_channels, topic, nsq_name)

    if all_matched:
        log_message = f"[LOG] Semua topik dan saluran yang dimonitor di {nsq_name} telah sesuai dengan config.ini.\n\n"
        print(log_message)
    else:
        alert_message = f"[ALERT] Terdapat ketidaksesuaian antara config.ini dan data di {nsq_name}."
        print(alert_message)
        send_telegram_alert(alert_message)

def send_telegram_alert(message):
    """Mengirim pesan alert ke Telegram menggunakan konfigurasi dari config.ini."""
    config = configparser.ConfigParser()
    config.read('config/config.ini')
    
    token = config.get('telegram', 'token')
    chat_id = config.get('telegram', 'chat_id')
    thread_id = config.get('telegram', 'thread_id')
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'message_thread_id': thread_id
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"[INFO] Alert dikirim ke Telegram: {message}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Gagal mengirim alert ke Telegram: {e}")


def read_config_broadcast_addresses(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    
    broadcast_addresses = {}
    for section in config.sections():
        if config.has_option(section, 'broadcast_address'):
            addresses = config.get(section, 'broadcast_address').split(', ')
            broadcast_addresses[section] = addresses
    
    return broadcast_addresses

def fetch_nodes_data(config):
    nodes_data = {}
    for section in config.sections():
        if config.has_option(section, 'nodes_address'):
            nodes_address = config.get(section, 'nodes_address')
            try:
                response = requests.get(nodes_address)
                if response.status_code == 200:
                    data = response.json()
                    nodes_data[section] = data
                    print(f"[INFO] Fetched data from {nodes_address} for section '{section}'")
                else:
                    print(f"[ERROR] Failed to fetch data from {nodes_address}: {response.status_code}")
            except Exception as e:
                print(f"[ERROR] Error fetching nodes for {section} at {nodes_address}: {e}")
    return nodes_data

def check_broadcast_addresses(nodes_data, config_broadcast_addresses):
    missing_addresses = {}
    for section, config_addresses in config_broadcast_addresses.items():
        nsq_addresses = []
        
        if section in nodes_data:
            producers = nodes_data[section].get('producers', []) if section == 'nsq_1' else nodes_data[section].get('data', {}).get('producers', [])
            nsq_addresses = [producer.get('broadcast_address') for producer in producers]
        
        missing_for_section = [addr for addr in config_addresses if addr not in nsq_addresses]
        if missing_for_section:
            missing_addresses[section] = missing_for_section
    
    return missing_addresses

