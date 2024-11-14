# main.py
from controller import read_config_broadcast_addresses, fetch_nodes_data, check_broadcast_addresses, send_telegram_alert
import configparser

if __name__ == "__main__":
    # Baca data `broadcast_address` dari config.ini
    config_file = 'config.ini'
    config_broadcast_addresses = read_config_broadcast_addresses(config_file)
    
    # Ambil data JSON dari setiap `nodes_address` di config.ini
    config = configparser.ConfigParser()
    config.read(config_file)
    nodes_data = fetch_nodes_data(config)

    # Periksa perbedaan `broadcast_address`
    missing_addresses = check_broadcast_addresses(nodes_data, config_broadcast_addresses)
    
    # Kirim alert jika ada `broadcast_address` yang hilang
    if missing_addresses:
        alert_message = "Peringatan: Ada `broadcast_address` yang hilang dari data NSQ:\n"
        for section, addresses in missing_addresses.items():
            alert_message += f"- Section {section}: {', '.join(addresses)}\n"
        print(alert_message)  # Debug print
        send_telegram_alert(alert_message)
    else:
        print("Semua `broadcast_address` sesuai dengan data NSQ.")
