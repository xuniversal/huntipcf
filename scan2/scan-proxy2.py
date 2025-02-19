import socket
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import ipaddress  # Untuk menangani rentang IP

# Rentang IP dan port
start_ip = "202.78.0.0"  # Ganti dengan IP awal
end_ip = "180.248.0.0"    # Ganti dengan IP akhir
start_port = 1              # Port awal
end_port = 65.535               # Port akhir

def Cek_proxy(ip, port, timeout=3):
    """Memeriksa koneksi IP dan PORT menggunakan socket"""
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except (socket.timeout, socket.error):
        return False

def Clear_file(filepath):
    """Menghapus isi file sebelum menulis data baru"""
    open(filepath, 'w').close()  # Buka file dengan 'w' untuk mengosongkannya

def Save_to_file(filepath, data, cache):
    """Simpan data ke file tanpa duplikasi"""
    if data not in cache:
        with open(filepath, 'a') as f:
            f.write(data + '\n')
        cache.add(data)  # Tambahkan ke cache untuk mencegah duplikasi

def Cek_ip_port(ip_address, port, save_path, active_cache, dead_cache):
    """Cek apakah proxy aktif atau tidak, lalu simpan hasilnya"""
    result = f"{ip_address},{port}"
    
    if Cek_proxy(ip_address, port):
        Save_to_file(os.path.join(save_path, "active.txt"), result, active_cache)
        print(f"[AKTIF] {result} ")
    else:
        Save_to_file(os.path.join(save_path, "dead.txt"), result, dead_cache)
        print(f"[TIDAK AKTIF] {result}")

def Read_ip_port(start_ip, end_ip, start_port, end_port, max_workers=100):
    """Cek status IP dan port dalam rentang yang diberikan dengan thread pool"""
    save_path = os.getcwd()  # Simpan di direktori kerja saat ini

    # Hapus isi file sebelum mulai
    Clear_file(os.path.join(save_path, "active.txt"))
    Clear_file(os.path.join(save_path, "dead.txt"))

    # Cache untuk mencegah duplikasi
    active_cache = set()
    dead_cache = set()

    # Menghasilkan rentang IP
    try:
        ip_range = [str(ip) for ip in ipaddress.summarize_address_range(ipaddress.IPv4Address(start_ip), ipaddress.IPv4Address(end_ip))]
        ip_list = []
        for ip in ip_range:
            ip_list.append(ip)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for ip in ip_list:
                for port in range(start_port, end_port + 1):
                    futures.append(executor.submit(Cek_ip_port, ip, port, save_path, active_cache, dead_cache))
            for future in as_completed(futures):
                future.result()  # Pastikan setiap tugas selesai

    except ValueError:
        print("Format IP salah. Pastikan IP valid.")

# Jalankan pengecekan proxy
Read_ip_port(start_ip, end_ip, start_port, end_port)
