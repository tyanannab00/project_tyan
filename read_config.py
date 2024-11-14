import configparser
import requests
import os
import time

def read_config_topics(file_path):
    """Membaca file config.ini dan mengumpulkan topik serta saluran."""
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

def get_nsq_data(nsq_address):
    """Mengambil data dari NSQ untuk mendapatkan topik dan channel."""
    try:
        response = requests.get(nsq_address)
        response.raise_for_status()
        nsq_data = response.json()
        
        # Menangani struktur JSON yang berbeda di setiap NSQ
        if 'data' in nsq_data:  
            topics = nsq_data['data'].get('topics', [])
        else:
            topics = nsq_data.get('topics', [])
        
        nsq_topics = {}
        for topic in topics:
            topic_name = topic['topic_name']
            channels = [ch['channel_name'] for ch in topic.get('channels', [])]
            nsq_topics[topic_name] = channels
        return nsq_topics
    
    except requests.exceptions.RequestException as e:
        print(f"Terjadi kesalahan saat menghubungi {nsq_address}: {e}")
        return None

def verify_topics_and_channels(config_topics, nsq_data, nsq_name):
    """Memverifikasi bahwa semua topik dan saluran di config.ini ada di data NSQ."""
    all_matched = True

    # Periksa apakah setiap topik dan saluran yang diinginkan ada di NSQ
    for topic, channels in config_topics.get(nsq_name, {}).items():
        if topic not in nsq_data:
            print(f"[ALERT] Topik '{topic}' tidak ditemukan di {nsq_name}.")
            all_matched = False
        else:
            # Periksa apakah setiap saluran yang diinginkan untuk topik ini ada di NSQ
            nsq_channels = set(nsq_data[topic])
            config_channels = set(channels)
            missing_channels = config_channels - nsq_channels
            extra_channels = nsq_channels - config_channels

            if missing_channels:
                print(f"[ALERT] Di {nsq_name}, channel '{missing_channels}' hilang dari topik '{topic}'.")
                all_matched = False
            if extra_channels:
                print(f"[ALERT] Di {nsq_name}, ada channel ekstra '{extra_channels}' dalam topik '{topic}'.")
                all_matched = False
            if not missing_channels and not extra_channels:
                print(f"[DEBUG] Semua channel yang diinginkan untuk topik '{topic}' ditemukan di {nsq_name}.")

    # Jika semua topik dan saluran sesuai, log bahwa semuanya sesuai
    if all_matched:
        print(f"[LOG] Semua topik dan saluran yang dimonitor di {nsq_name} telah sesuai dengan config.ini.")
    else:
        print(f"[ALERT] Terdapat ketidaksesuaian antara config.ini dan data di {nsq_name}.")

if __name__ == "__main__":
    # Path ke file config.ini
    config_file_path = os.path.join('config', 'config.ini')
    
    # Membaca konfigurasi NSQ address dari config.ini
    config = configparser.ConfigParser()
    config.read(config_file_path)
    nsq_address_1 = config.get('nsq_1', 'nsq_address')
    nsq_address_2 = config.get('nsq_2', 'nsq_address')

    # Loop untuk pengecekan setiap 5 menit
    while True:
        print("\n[INFO] Memulai pengecekan topik dan saluran NSQ...")

        # Membaca topik dan saluran dari config.ini
        config_topics = read_config_topics(config_file_path)
        
        # Mendapatkan data NSQ
        nsq_data_1 = get_nsq_data(nsq_address_1)
        nsq_data_2 = get_nsq_data(nsq_address_2)
        
        # Memverifikasi topik dan saluran berdasarkan data dari config.ini
        if nsq_data_1:
            print(f"[DEBUG] Data aktual dari NSQ 1: {nsq_data_1}")
            verify_topics_and_channels(config_topics, nsq_data_1, 'nsq_1')
        if nsq_data_2:
            print(f"[DEBUG] Data aktual dari NSQ 2: {nsq_data_2}")
            verify_topics_and_channels(config_topics, nsq_data_2, 'nsq_2')
        
        print("[INFO] Pengecekan selesai. Menunggu 5 menit sebelum pengecekan berikutnya...\n")
        time.sleep(300)  # Menunggu 5 menit (300 detik) sebelum pengecekan berikutnya
