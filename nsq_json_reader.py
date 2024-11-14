import requests
import configparser
import json

def get_nsq_address_from_config(config_file, section):
    # Membaca file konfigurasi
    config = configparser.ConfigParser()
    config.read(config_file)
    
    # Mengambil nilai 'nsq_address' dari section yang diberikan
    if config.has_section(section):
        return config.get(section, 'nsq_address')
    else:
        print(f"Section '{section}' tidak ditemukan dalam {config_file}.")
        return None

def display_nsq_json(nsq_address):
    try:
        # Mengambil data JSON dari URL
        response = requests.get(nsq_address)
        response.raise_for_status()  # Memastikan respons status adalah OK (200)

        # Parsing JSON dari response
        nsq_data = response.json()

        # Menampilkan data JSON dengan format yang rapi
        print(json.dumps(nsq_data))
    
    except requests.exceptions.RequestException as e:
        print(f"Terjadi kesalahan saat menghubungi {nsq_address}: {e}")
    except ValueError as e:
        print(f"Gagal parsing JSON dari {nsq_address}: {e}")

if __name__ == "__main__":
    config_file = 'config/config.ini'  # Nama file konfigurasi
    section = 'nsq_1'  # Section yang ingin dibaca

    # Mendapatkan nsq_address dari file konfigurasi
    nsq_address = get_nsq_address_from_config(config_file, section)

    if nsq_address:
        print(f"Menampilkan data JSON dari: {nsq_address}")
        display_nsq_json(nsq_address)
