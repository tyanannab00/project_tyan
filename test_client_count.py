import configparser
import requests
import os
import time

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
        
        # Menangani struktur JSON yang berbeda di setiap NSQ
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
                if check_client_count:  # Hanya cek client_count untuk NSQ 1
                    # Cek apakah 'client_count' ada di dalam data channel
                    client_count = channel.get('client_count', 0)  # Gunakan 0 sebagai default jika client_count tidak ada
                    channel_info.append({
                        'channel_name': channel['channel_name'],
                        'client_count': client_count
                    })
                    
                    # Log jumlah client_count untuk setiap channel
                    print(f"[INFO] Topik '{topic_name}', Channel '{channel['channel_name']}': client_count = {client_count}")
                    
                    # Jika ada client_count yang berjumlah 0, beri alert
                    if client_count == 0:
                        print(f"[ALERT] Topik '{topic_name}', Channel '{channel['channel_name']}' memiliki client_count = 0!")
                else:
                    # Tidak mengecek client_count untuk NSQ 2
                    channel_info.append({
                        'channel_name': channel['channel_name']
                    })
            
            nsq_topics[topic_name] = channel_info
        return nsq_topics
    
    except requests.exceptions.RequestException as e:
        print(f"Terjadi kesalahan saat menghubungi {nsq_address}: {e}")
        return None

def compare_sets(config_set, nsq_set, section, nsq_name):
    """Memeriksa apakah ada perbedaan antara set saluran dan memberikan alert."""
    missing_in_nsq = config_set - nsq_set
    extra_in_nsq = nsq_set - config_set

    if missing_in_nsq:
        print(f"[ALERT] Di {nsq_name}, channel '{missing_in_nsq}' hilang dari topik '{section}'")
    if extra_in_nsq:
        print(f"[ALERT] Di {nsq_name}, ada channel ekstra '{extra_in_nsq}' dalam topik '{section}'")

def verify_topics_and_channels(config_topics, nsq_data, nsq_name, check_client_count=False):
    """Memverifikasi kesesuaian topik dan saluran antara config.ini dan data NSQ."""
    all_matched = True

    # Membandingkan topik dan saluran yang ada pada config dengan data NSQ
    for topic, channels in config_topics.get(nsq_name, {}).items():
        if topic not in nsq_data:
            print(f"[ALERT] Topik '{topic}' tidak ditemukan di {nsq_name}.")
            all_matched = False
        else:
            # Gunakan perbandingan set untuk channel
            nsq_channels = set(nsq_data[topic])
            config_channels = set(channels)
            
            # Bandingkan menggunakan fungsi perbandingan set
            compare_sets(config_channels, nsq_channels, topic, nsq_name)

    # Log jika semua topik dan channel sesuai
    if all_matched:
        print(f"[LOG] Semua topik dan saluran yang dimonitor di {nsq_name} telah sesuai dengan config.ini.\n\n")
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
        
        # Mendapatkan data NSQ 1 dengan pengecekan client_count
        nsq_data_1 = get_nsq_data(nsq_address_1, check_client_count=True)
        
        # Mendapatkan data NSQ 2 tanpa pengecekan client_count
        nsq_data_2 = get_nsq_data(nsq_address_2, check_client_count=False)
        
        # Memverifikasi topik dan saluran berdasarkan data dari config.ini
        if nsq_data_1:
            print(f"\n[DEBUG] Data aktual dari NSQ 1: {nsq_data_1}")
            verify_topics_and_channels(config_topics, nsq_data_1, 'nsq_1', check_client_count=True)
        if nsq_data_2:
            print(f"[DEBUG] Data aktual dari NSQ 2: {nsq_data_2}")
            verify_topics_and_channels(config_topics, nsq_data_2, 'nsq_2', check_client_count=False)
        
        print("[INFO] Pengecekan selesai. Menunggu 5 menit sebelum pengecekan berikutnya...\n")
        time.sleep(300)  # Menunggu 5 menit (300 detik) sebelum pengecekan berikutnya
