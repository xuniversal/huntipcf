import socket
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# File input yang berisi daftar proxy
file_input = "scan/rawProxyList.txt"
# Token API ipinfo.io (opsional, gunakan jika memiliki akun premium untuk menghindari rate limit)
IPINFO_TOKEN = ""  # Contoh: "123456789abcdef"

def Cek_proxy(ip, port, timeout=3):
    """Memeriksa koneksi IP dan PORT menggunakan socket"""
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except (socket.timeout, socket.error):
        return False

def Get_ASN(ip, cache_asn):
    """Mengambil informasi ASN dari ipinfo.io dengan caching"""
    if ip in cache_asn:
        return cache_asn[ip]
    
    try:
        url = f"https://ipinfo.io/{ip}/json"
        if IPINFO_TOKEN:
            url += f"?token={IPINFO_TOKEN}"
        
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            asn = data.get("org", "")
            cache_asn[ip] = asn
            return asn
    except requests.RequestException:
        pass  # Jika API gagal, lanjutkan tanpa error
    
    return ""

def Is_Cloudflare(ip, cache_asn):
    """Cek apakah IP menggunakan Cloudflare berdasarkan ASN"""
    asn = Get_ASN(ip, cache_asn)
    return "AS13335" in asn  # Cloudflare ASN

def Clear_file(filepath):
    """Menghapus isi file sebelum menulis data baru"""
    open(filepath, 'w').close()

def Save_to_file(filepath, data, cache):
    """Simpan data ke file tanpa duplikasi"""
    if data not in cache:
        with open(filepath, 'a') as f:
            f.write(data + '\n')
        cache.add(data)

def Cek_ip_port(line, save_path, active_cache, dead_cache, cloudflare_cache, cache_asn):
    """Cek apakah proxy aktif atau tidak, lalu simpan hasilnya"""
    parts = line.strip().split(',')
    if len(parts) >= 2:
        ip_address = parts[0]
        try:
            port_number = int(parts[1])
        except ValueError:
            print(f"[ERROR] Port tidak valid : {parts[1]}")
            return
        
        country = parts[2] if len(parts) > 2 else "Unknown"
        organization = parts[3] if len(parts) > 3 else "Unknown"
        
        result = f"{ip_address},{port_number},{country},{organization}"
        
        if Cek_proxy(ip_address, port_number):
            Save_to_file(os.path.join(save_path, "active.txt"), result, active_cache)
            print(f"[AKTIF] {result}")
            
            if Is_Cloudflare(ip_address, cache_asn):
                Save_to_file(os.path.join(save_path, "cloudflare.txt"), result, cloudflare_cache)
                print(f"[CLOUDFLARE] {result}")
        else:
            Save_to_file(os.path.join(save_path, "dead.txt"), result, dead_cache)
            print(f"[TIDAK AKTIF] {result}")

def Read_ip_port(filename, max_workers=100):
    """Baca IP dan port dari file, lalu cek statusnya dengan thread pool"""
    save_path = os.path.dirname(filename)  # Ambil folder dari file_input

    # Hapus isi file sebelum mulai
    Clear_file(os.path.join(save_path, "active.txt"))
    Clear_file(os.path.join(save_path, "dead.txt"))
    Clear_file(os.path.join(save_path, "cloudflare.txt"))

    # Cache untuk mencegah duplikasi
    active_cache = set()
    dead_cache = set()
    cloudflare_cache = set()
    cache_asn = {}  # Cache untuk menyimpan ASN berdasarkan IP

    try:
        with open(filename, 'r') as file:
            lines = file.readlines()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(Cek_ip_port, line, save_path, active_cache, dead_cache, cloudflare_cache, cache_asn) for line in lines]
            for future in as_completed(futures):
                future.result()

    except FileNotFoundError:
        print(f"File '{filename}' tidak ditemukan.")
    except ValueError:
        print("Format data salah. Pastikan IP dan port dipisah dengan koma.")

# Jalankan pengecekan proxy
Read_ip_port(file_input)
