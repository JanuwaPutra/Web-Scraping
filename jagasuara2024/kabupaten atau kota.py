import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import os


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
        for index, col in enumerate(cols):
            text = col.text.strip()
            if index == 0:  # Kolom pertama (Kabupaten/Kota) mengandung link
                cols_data.append(text)
            else:
                cols_data.append(text)

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
    writer.writerow( headers )  # Menambahkan kolom 'Province ID' dan 'Link'
    
    # Menulis data yang sudah diambil, dengan menyertakan province_id untuk setiap baris
    for row in all_data:
        writer.writerow(row)  # Menambahkan province_id ke setiap baris data

print(f"Data telah disimpan ke {filename}")

# Fungsi untuk scrape halaman utama dan ambil link kabupaten
def scrape_main_page(url):
    driver.get(url)
    time.sleep(5)  # Tunggu beberapa detik untuk memastikan halaman dimuat

    # Ambil tabel
    table = driver.find_element(By.XPATH, '//table[@class="table-auto w-full text-center"]')
    rows = table.find_elements(By.XPATH, './/tbody/tr')

    kabupaten_links = []

    for row in rows:
        kabupaten_name_col = row.find_element(By.XPATH, './/td[1]/a')
        kabupaten_name = kabupaten_name_col.text.strip()
        kabupaten_link = kabupaten_name_col.get_attribute('href')
        kabupaten_links.append((kabupaten_name, kabupaten_link))

    return kabupaten_links

# Fungsi untuk scrape halaman kabupaten
# Scrape halaman kabupaten
def scrape_kabupaten_page(kabupaten_url):
    driver.get(kabupaten_url)
    time.sleep(5)  # Tunggu beberapa detik untuk memastikan halaman dimuat

    # Ambil tabel dari halaman kabupaten
    table = driver.find_element(By.XPATH, '//div[@class="flex flex-row justify-center"]//table')
    
    # Ambil header (kolom) dari tabel
    headers = table.find_elements(By.XPATH, './/thead//th')
    header_names = []  # Pastikan variabel ini digunakan

    for header in headers:
        header_text = header.text.strip()
        links = header.find_elements(By.TAG_NAME, 'a')
        if len(links) == 2:  # Jika ada dua kandidat
            candidate_1 = links[0].text.strip()
            candidate_2 = links[1].text.strip()
            header_names.append(f"{candidate_1} - {candidate_2}")
            header_names.append(f"{candidate_1} - {candidate_2}")  # Kolom baru dengan nama yang sama
        elif header_text:  # Jika hanya ada satu nama atau teks biasa
            header_names.append(header_text)

    # Ambil data (baris) dari tabel
    rows = table.find_elements(By.XPATH, './/tbody/tr')
    data = []

    for row in rows:
        cols = row.find_elements(By.XPATH, './/td')
        cols_data = []
        links_data = []  # Menyimpan link URL untuk setiap baris
        for index, col in enumerate(cols):
            text = col.text.strip()
            if index == 0:  # Kolom pertama (Kabupaten/Kota) mengandung link
                link_kecamatan = col.find_element(By.TAG_NAME, 'a').get_attribute('href') if col.find_elements(By.TAG_NAME, 'a') else ""
                links_data.append(link_kecamatan)  # Menambahkan link
                cols_data.append(text)
            else:
                cols_data.append(text)

        cols_data.extend(links_data)  # Gabungkan data dengan link
        data.append(cols_data)

    return header_names, data

# Ambil link kabupaten dari halaman utama
kabupaten_links = scrape_main_page(url)

# Loop untuk setiap link kabupaten dan scrape halaman detailnya
for kabupaten_name, kabupaten_link in kabupaten_links:
    print(f"Scraping {kabupaten_name}...")
    headers, data = scrape_kabupaten_page(kabupaten_link)  # Pastikan header dari fungsi ini digunakan

    # Membuat nama file CSV berdasarkan nama kabupaten
    filename = f"{kabupaten_name} data.csv"
    
    
    # Membuat nama folder dan memastikan folder tersebut ada
    folder_name = "kabupaten Atau Kota"
    os.makedirs(folder_name, exist_ok=True)

    # Membuat nama file CSV berdasarkan nama kabupaten di dalam folder
    filename = os.path.join(folder_name, f"{kabupaten_name} data.csv")

    # Menyimpan data ke CSV
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Menulis header yang diambil dari elemen <th>
        writer.writerow(headers + ['Link'])  # Gunakan header dari fungsi `scrape_kabupaten_page`
        
        # Menulis data
        for row in data:
            writer.writerow(row)

        print(f"Data untuk kabupaten {kabupaten_name} telah disimpan ke {filename}")

# Tutup browser setelah selesai
driver.quit()
