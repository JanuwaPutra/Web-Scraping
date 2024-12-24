import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Setup WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Menjalankan di background
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# URL halaman utama
url = "https://jagasuara2024.org/main/rekapitulasi/gubernur/provinsi?id=74"

# Fungsi untuk scrape halaman utama dan ambil link kecamatan
def scrape_main_page(url):
    driver.get(url)
    time.sleep(5)  # Tunggu beberapa detik untuk memastikan halaman dimuat

    # Ambil tabel
    table = driver.find_element(By.XPATH, '//table[@class="table-auto w-full text-center"]')
    rows = table.find_elements(By.XPATH, './/tbody/tr')

    kecamatan_links = []

    for row in rows:
        kecamatan_name_col = row.find_element(By.XPATH, './/td[1]/a')
        kecamatan_name = kecamatan_name_col.text.strip()
        kecamatan_link = kecamatan_name_col.get_attribute('href')
        kecamatan_links.append((kecamatan_name, kecamatan_link))

    return kecamatan_links

# Fungsi untuk scrape halaman kecamatan
def scrape_kecamatan_page(kecamatan_url):
    driver.get(kecamatan_url)
    time.sleep(5)  # Tunggu beberapa detik untuk memastikan halaman dimuat

    # Ambil tabel dari halaman kecamatan
    table = driver.find_element(By.XPATH, '//div[@class="flex flex-row justify-center"]//table')
    
    # Ambil header (kolom) dari tabel
    headers = table.find_elements(By.XPATH, './/thead//th')
    header_names = [header.text.strip() for header in headers]

    # Ambil data (baris) dari tabel
    rows = table.find_elements(By.XPATH, './/tbody/tr')

    data = []
    for row in rows:
        cols = row.find_elements(By.XPATH, './/td')
        if len(cols) > 1:  # Pastikan baris memiliki data
            cols_data = [col.text.strip() for col in cols]
            data.append(cols_data)

    return header_names, data

# Ambil link kecamatan dari halaman utama
kecamatan_links = scrape_main_page(url)

# Loop untuk setiap link kecamatan dan scrape halaman detailnya
for kecamatan_name, kecamatan_link in kecamatan_links:
    print(f"Scraping {kecamatan_name}...")
    headers, data = scrape_kecamatan_page(kecamatan_link)

    # Membuat nama file CSV berdasarkan nama kecamatan
    filename = f"{kecamatan_name.replace(' ', '_')}_data.csv"

    # Menyimpan data ke CSV
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Menulis header yang diambil dari elemen <th>
        writer.writerow(headers)
        
        # Menulis data
        for row in data:
            writer.writerow(row)

    print(f"Data untuk kecamatan {kecamatan_name} telah disimpan ke {filename}")

# Tutup browser setelah selesai
driver.quit()
