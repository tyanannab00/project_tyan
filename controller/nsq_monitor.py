# controllers/nsq_monitor.py

import requests
import configparser
import os

# Load konfigurasi dari config.ini
config = configparser.ConfigParser()
config.read(os.path.join('config', 'config.ini'))

def fetch_nodes_data():
    """Mengambil response JSON dari setiap nodes_address yang didefinisikan di config.ini."""
    nodes_data = {}

    for section in config.sections():
        if 'nodes_address' in config[section]:
            nodes_address = config[section]['nodes_address']
            try:
                response = requests.get(nodes_address)
                response.raise_for_status()
                data = response.json()
                nodes_data[section] = data  # Simpan data JSON di dictionary dengan nama section
                print(f"[INFO] Data berhasil diambil dari {section}: {nodes_address}")
            except requests.exceptions.RequestException as e:
                print(f"[ERROR] Gagal mengambil data dari {section}: {nodes_address}. Error: {e}")

    return nodes_data
