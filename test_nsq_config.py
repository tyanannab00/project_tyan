import configparser
import os

def read_config(file_path):
    # Membaca file config.ini
    config = configparser.ConfigParser()
    config.read(file_path)
    
    # Menampilkan isi dari file config.ini tanpa membaca nsq_address
    for section in config.sections():
        print(f"[{section}]")
        for key, value in config.items(section):
            if key != "nsq_address":  # Pengecualian untuk 'nsq_address'
                print(f"{key} = {value}")
        print()  # Menambahkan baris kosong antar bagian

# Path ke file config.ini dengan folder 'config'
config_file_path = os.path.join('config', 'config.ini')

# Memanggil fungsi untuk membaca dan menampilkan konfigurasi
read_config(config_file_path)
