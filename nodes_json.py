# main.py
from controller import read_config_broadcast_addresses, fetch_nodes_data, check_broadcast_addresses, send_telegram_alert
import configparser
import time

def main():
    config_file = 'config.ini'
    config_broadcast_addresses = read_config_broadcast_addresses(config_file)
    
    # Ambil data JSON dari setiap `nodes_address` di config.ini
    config = configparser.ConfigParser()
    config.read(config_file)

    while True:
        print("[INFO] Memulai pengecekan NSQ nodes...")
        nodes_data = fetch_nodes_data(config)
        
        # Periksa perbedaan `broadcast_address`
        missing_addresses = check_broadcast_addresses(nodes_data, config_broadcast_addresses)
        
        # Log hasil pemeriksaan per `nodes_address`
        for section, addresses in config_broadcast_addresses.items():
            if section in nodes_data:
                print(f"[INFO] NSQ check for '{section}' ({config.get(section, 'nodes_address')}): OK")
            else:
                print(f"[WARNING] Tidak ada data NSQ untuk '{section}'.")

        # Kirim alert jika ada `broadcast_address` yang hilang
        if missing_addresses:
            alert_message = "Peringatan: Ada `broadcast_address` yang hilang dari data NSQ:\n"
            for section, addresses in missing_addresses.items():
                alert_message += f"- Section {section}: {', '.join(addresses)}\n"
            print(f"[ALERT] {alert_message}")
            send_telegram_alert(alert_message)
        else:
            print("[INFO] Semua `broadcast_address` sesuai dengan data NSQ.")
        
        # Tunggu selama 5 menit (300 detik) sebelum pengecekan berikutnya
        time.sleep(300)

if __name__ == "__main__":
    main()
