import os
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Folder input dan output
input_folder = "kecamatan"  # Folder tempat file CSV input
output_folder = "kelurahan"  # Folder untuk menyimpan hasil scraping

# Setup Selenium WebDriver
options = Options()
options.add_argument("--headless")  # Jalankan browser di mode headless
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Membuat folder output jika belum ada
os.makedirs(output_folder, exist_ok=True)

# Menelusuri semua folder dan subfolder untuk mencari file CSV
for root, dirs, files in os.walk(input_folder):
    for file_name in files:
        if file_name.endswith(".csv"):  # Hanya memproses file CSV
            input_csv = os.path.join(root, file_name)

            # Membaca isi file CSV
            with open(input_csv, mode="r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    kecamatan_name = row["Kelurahan"]
                    link = row["Link"]

                    # Buka halaman link
                    driver.get(link)
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "table-auto"))
                    )

                    # Scraping data tabel
                    table = driver.find_element(By.CLASS_NAME, "table-auto")
                    
                    # Ambil header (kolom) dari tabel
                    headers = table.find_elements(By.XPATH, './/thead//th')
                    header_names = []  # Variabel untuk menyimpan nama header

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

                    # Tambahkan kolom "Link" ke dalam header jika belum ada
                    if "Link" not in header_names:
                        header_names.append("Link")

                    rows = []

                    # Iterasi setiap baris data di tabel
                    for tr in table.find_elements(By.XPATH, ".//tbody/tr"):
                        row_data = [td.text.strip() for td in tr.find_elements(By.XPATH, ".//td")]

                        # Cari link dari elemen <a> di kolom kecamatan
                        link_element = tr.find_element(By.XPATH, ".//td/a")
                        link_url = link_element.get_attribute("href")

                        # Tambahkan link ke baris data
                        row_data.append(link_url)
                        rows.append(row_data)

                    # Membuat folder berdasarkan nama CSV dari folder input di dalam folder output
                    # Nama folder berdasarkan nama file CSV (misalnya KAB. BOMBANA_DATA)
                    kecamatan_folder = os.path.join(output_folder, f"{file_name.replace('.csv', '').replace(' ', '_')}_DATA")
                    os.makedirs(kecamatan_folder, exist_ok=True)

                    # Menyimpan data ke CSV di dalam folder kecamatan
                    output_csv = os.path.join(kecamatan_folder, f"{kecamatan_name.replace(' ', '_')}.csv")
                    with open(output_csv, mode="w", newline="", encoding="utf-8") as out_file:
                        writer = csv.writer(out_file)
                        writer.writerow(header_names)  # Header
                        writer.writerows(rows)  # Data

                    print(f"Data untuk {kecamatan_name} telah disimpan di {output_csv}")

# Tutup browser
driver.quit()
