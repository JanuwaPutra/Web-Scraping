import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

# Setup WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Menjalankan di background
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# URL yang ingin di-scrape
urls = [
    "https://jagasuara2024.org/main/rekapitulasi/gubernur/provinsi?id=74"
]

# Fungsi untuk scrape data dari halaman
def scrape_data(url):
    driver.get(url)
    time.sleep(5)  # Tunggu beberapa detik untuk memastikan halaman dimuat

    # Ambil header kolom dari elemen <thead>
    thead = driver.find_element(By.XPATH, '//table[@class="table-auto w-full text-center"]/thead')
    header_cols = thead.find_elements(By.XPATH, './/th')
    headers = []

    # Proses header kolom yang ada
    for header in header_cols:
        header_text = header.text.strip()
        
        # Cek apakah header tersebut berisi dua nama (dalam satu kolom)
        links = header.find_elements(By.TAG_NAME, 'a')
        if len(links) == 2:  # Jika ada dua kandidat
            candidate_1 = links[0].text.strip()
            candidate_2 = links[1].text.strip()
            # Menambahkan nama kandidat dua kali di header untuk kolom baru
            headers.append(f"{candidate_1} - {candidate_2}")
            headers.append(f"{candidate_1} - {candidate_2}")  # Kolom baru dengan nama yang sama
        elif header_text:  # Jika hanya ada satu nama atau teks biasa
            headers.append(header_text)

    # Ambil tabel
    tabel = driver.find_element(By.XPATH, '//table[@class="table-auto w-full text-center"]')
    rows = tabel.find_elements(By.XPATH, './/tbody/tr')
    
    data = []
    for row in rows:
        cols = row.find_elements(By.XPATH, './/td')
        cols_data = []
        links_data = []  # Menyimpan link URL untuk setiap baris
        for index, col in enumerate(cols):
            text = col.text.strip()
            if index == 0:  # Kolom pertama (Kabupaten/Kota) mengandung link
                link = col.find_element(By.TAG_NAME, 'a').get_attribute('href') if col.find_elements(By.TAG_NAME, 'a') else ""
                links_data.append(link)  # Menambahkan link
                cols_data.append(text)
            else:
                cols_data.append(text)

        cols_data.extend(links_data)  # Gabungkan data dengan link
        data.append(cols_data)

    return headers, data

# Menyusun nama file berdasarkan URL
def extract_province_id(url):
    match = re.search(r'provinsi\?id=(\d+)', url)
    return match.group(1) if match else "unknown"

# Scrape data dari semua URL yang ditentukan
all_data = []
headers = []
for url in urls:
    page_headers, data = scrape_data(url)
    headers = page_headers  # Ambil header hanya dari halaman pertama, asumsikan header sama untuk semua
    all_data.extend(data)  # Gabungkan data dari setiap halaman

# Ambil ID provinsi dari URL untuk menyesuaikan nama file
province_id = extract_province_id(urls[0])
filename = f"Provinsi_{province_id}.csv"  # Menyesuaikan nama file dengan ID provinsi

# Menyimpan data ke CSV
with open(filename, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    
    # Menulis header yang diambil otomatis dari <thead>
    writer.writerow(['Province ID'] + headers + ['Link'])  # Menambahkan kolom 'Province ID' dan 'Link'
    
    # Menulis data yang sudah diambil, dengan menyertakan province_id untuk setiap baris
    for row in all_data:
        writer.writerow([province_id] + row)  # Menambahkan province_id ke setiap baris data

print(f"Data telah disimpan ke {filename}")

# Tutup browser setelah selesai
driver.quit()
