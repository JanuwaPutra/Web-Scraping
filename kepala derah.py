from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import csv
import time
import traceback
import re
import os

def extract_profile_data(soup):
    """Ekstrak data profil dari HTML."""
    profile_data = {}
    profile_data['nama'] = soup.find('h4').text.strip()  # Assuming name is in h4 tag
    
    # Ekstrak informasi dasar
    rows = soup.find_all('div', class_='row')[1].find_all('p')
    for row in rows:
        key = row.find('strong').text.replace(':', '').strip()
        value = row.text.replace(row.find('strong').text, '').replace(':', '').strip()
        profile_data[key] = value
    
    # Ekstrak pekerjaan
    pekerjaan = soup.find('ul', class_='text-left')
    if pekerjaan and pekerjaan.find('li'):
        profile_data['Pekerjaan'] = pekerjaan.find('li').text.strip()
    
    # Ekstrak status hukum
    status_hukum_section = soup.find_all('div', class_='row')[3]  # Section containing status hukum
    if status_hukum_section:
        status_hukum_ul = status_hukum_section.find('ul', class_='text-left')
        if status_hukum_ul and status_hukum_ul.find('li'):
            profile_data['Status Hukum'] = status_hukum_ul.find('li').text.strip()
        else:
            profile_data['Status Hukum'] = 'Data tidak ada'
    
    return profile_data

def extract_table_data(soup, table_title):
    """Ekstrak data dari tabel berdasarkan judul."""
    tables = soup.find_all('table', class_='table-bordered')
    for table in tables:
        header = table.find('tr').text.strip()
        if table_title in header:
            rows = []
            header_row = [th.text.strip() for th in table.find_all('tr')[1].find_all('th')]
            rows.append(header_row)
            
            for row in table.find_all('tr')[2:]:
                cells = [td.text.strip() for td in row.find_all('td')]
                if not all(cell == 'Data tidak ada' for cell in cells):
                    rows.append(cells)
            
            return rows
    return []
def scrape_kpu_data():
    # Konfigurasi Chrome WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        jenis_pemilihan = "Walikota"
        provinsi = "KOTA PROBOLINGGO"
        # Buka halaman web
        driver.get('https://infopemilu.kpu.go.id/Pemilihan/Pasangan_calon')

        # Pilih jenis pemilihan Gubernur
        jenis_pemilihan_select = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, 'jenis_pemilihan'))
        )
        jenis_pemilihan_select.click()
        driver.find_element(By.XPATH, f"//option[@value='{jenis_pemilihan}']").click()

        # Pilih wilayah Provinsi Jawa Timur
        wilayah_select = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//span[@id='select2-wilayah-container']"))
        )
        wilayah_select.click()
        time.sleep(2)
        search_box = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//input[@class='select2-search__field']"))
        )
        search_box.send_keys(f"{provinsi}")
        time.sleep(2)
        option = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, f"//li[contains(@class, 'select2-results__option') and text()='{provinsi}']"))
        )
        option.click()

        # Klik tombol filter
        filter_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, 'filter-btn'))
        )
        filter_button.click()

        # Tunggu dan scroll halaman
        time.sleep(5)
        driver.execute_script("window.scrollBy(0, window.innerHeight / 1);")
        time.sleep(5)

        # Tentukan folder utama
        folder_path = f"Data Kepala Daerah {jenis_pemilihan} {provinsi} "
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)  # Membuat folder jika belum ada
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'modal.fade'))
        )

        # Dapatkan HTML dari seluruh halaman
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Temukan semua elemen modal
        modals = driver.find_elements(By.CLASS_NAME, 'modal.fade')

        for index, modal in enumerate(modals):
            # Ekstrak HTML dari modal
            modal_soup = BeautifulSoup(modal.get_attribute('outerHTML'), 'html.parser')

            # Ekstrak nama dari modal
            name_element = modal_soup.find('h4')  # Adjust tag if name is elsewhere
            name = name_element.get_text(strip=True) if name_element else f"Unknown Name {index}"

            # Ekstrak dan simpan data profil untuk setiap modal
            profile_data = extract_profile_data(modal_soup)
            
            # Create a list of field names and values
            fields = list(profile_data.keys())
            values = list(profile_data.values())

            # Tentukan nomor berdasarkan index
            nomor = (index // 2) + 1  # Adjust numbering logic based on your requirement
            
            subfolder_path = os.path.join(folder_path, f"Nomor {nomor}")  # Nomor mulai dari 1
            if not os.path.exists(subfolder_path):
                os.makedirs(subfolder_path)  # Membuat folder untuk calon jika belum ada
                
            # Tentukan nama file CSV dengan format yang diinginkan
            filename = os.path.join(subfolder_path, f'profile_{name}.csv')
            # Save to CSV with fields as columns
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(fields)  # Write header with field names
                writer.writerow(values)  # Write values in the next row

            # Ekstrak dan simpan data tabel untuk setiap modal
            table_titles = [
                'Riwayat Pendidikan',
                'Riwayat Kursus/Diklat',
                'Riwayat Organisasi',
                'Riwayat Tanda Penghargaan',
                'Riwayat Publikasi'
            ]
            
            for title in table_titles:
                data = extract_table_data(modal_soup, title)
                if data:
                    filename = os.path.join(subfolder_path, f"{title.lower().replace('/', '_').replace(' ', '_')}_{name}.csv")
                    with open(filename, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        # Add the name only once in the header row
                        writer.writerow(['Nama'] + [column for column in data[0]])  # Header with 'Nama'
                        
                        # Add the name only for the first data row
                        for i, row in enumerate(data):
                            if i == 0:  # For the first row, include the name
                                writer.writerow([name] + row)  # Add name as the first column in the first row
                            else:  # For subsequent rows, do not include the name
                                writer.writerow([''] + row)  # Leave the name field empty

        
        
        visi_misi_elements = driver.find_elements(By.CLASS_NAME, 'visi-misi')
        party_elements = driver.find_elements(By.CLASS_NAME, 'party')

        # Data untuk setiap elemen
        data_elements = []

        # Iterasi melalui elemen
        for idx, (visi_misi, party) in enumerate(zip(visi_misi_elements, party_elements), start=1):
            # Ambil visi dan misi
            visi = visi_misi.find_element(By.XPATH, ".//h5[text()='Visi']/following-sibling::p").text
            misi = visi_misi.find_element(By.XPATH, ".//h5[text()='Misi']/following-sibling::p").text

            # Ambil nama partai
            partai_images = party.find_elements(By.TAG_NAME, "img")
            partai_names = [img.get_attribute("alt") for img in partai_images]

            # Tambahkan ke data elemen terkait
            data_elements.append({
                'Visi': visi,
                'Misi': misi,
                'Partai': ", ".join(partai_names)  # Gabungkan nama partai dengan koma
            })

        # Simpan data setiap elemen ke file CSV terpisah dalam folder masing-masing
        for index, data in enumerate(data_elements):
            
            # Tentukan folder untuk calon tertentu, sesuai dengan nomor calon
            subfolder_path = os.path.join(folder_path, f"Nomor {index + 1}")  # Nomor mulai dari 1
            if not os.path.exists(subfolder_path):
                os.makedirs(subfolder_path)  # Membuat folder untuk calon jika belum ada
                
            # Tentukan nama file CSV dengan format yang diinginkan
            filename = os.path.join(subfolder_path, f"visi misi dan nama partai.csv")
            
            # Menyimpan file CSV
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=['Visi', 'Misi', 'Partai'])
                writer.writeheader()
                writer.writerows([data])  # data adalah sebuah dictionary untuk satu calon
            print(f"Data elemen {index + 1} berhasil disimpan ke {filename}")

        # Ambil semua tombol kampanye di halaman awal
        kampanye_buttons = driver.find_elements(By.XPATH, "//form[@action='Pasangan_calon/kampanye']//button[@type='submit']")
        print(f"Jumlah tombol kampanye ditemukan: {len(kampanye_buttons)}")

        for index in range(len(kampanye_buttons)):
            if index == 3 or index == 4:
                driver.execute_script("window.scrollBy(0, window.innerHeight / 1);")
                time.sleep(1)
                driver.execute_script("window.scrollBy(0, window.innerHeight / 2);")
                time.sleep(3)
            # Refresh elemen tombol (karena DOM berubah setelah navigasi kembali)
            kampanye_buttons = driver.find_elements(By.XPATH, "//form[@action='Pasangan_calon/kampanye']//button[@type='submit']")
            kampanye_button = kampanye_buttons[index]
            # Klik tombol kampanye
            kampanye_button.click()
            subfolder_path = os.path.join(folder_path, f"Nomor {index + 1}")  # Nomor mulai dari 1
            if not os.path.exists(subfolder_path):
                os.makedirs(subfolder_path)  # Membuat folder untuk calon jika belum ada
            # Tunggu hingga halaman kampanye dimuat
            time.sleep(5)
        
            # Debug: Scrape data dari halaman tujuan
            print(f"Scraping data dari tombol kampanye ke-{index + 1}")
            # Tambahkan logika scraping Anda di sini

            # Cari semua tabel
            tables = driver.find_elements(By.TAG_NAME, "table")
            print(f"Number of tables found: {len(tables)}")
    
            # Scrape data tabel Laporan Kampanye (Tabel pertama)
            kampanye_tables = driver.find_elements(By.XPATH, "//table[@id='tbl_keanggotaan']")
            print(f"Number of tables with id 'tbl_keanggotaan': {len(kampanye_tables)}")
    
            if len(kampanye_tables) >= 1:
                kampanye_table = kampanye_tables[0]
                kampanye_rows = kampanye_table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header row
                kampanye_data = []
                for row in kampanye_rows:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    kampanye_data.append([col.text for col in cols])
    
                # Simpan ke CSV Laporan Kampanye dengan nama yang berbeda berdasarkan index
                with open(os.path.join(subfolder_path, f"laporan kampanye calon{index + 1}.csv"), "w", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow(["Tanggal", "Metode", "Tempat", "Kegiatan", "Jumlah Peserta", "Status Pelaksanaan"])
                    writer.writerows(kampanye_data)

                print(f"Data Laporan Kampanye {index + 1} berhasil disimpan.")
    
            # Scrape data tabel Laporan APK (Tabel kedua)
            if len(kampanye_tables) >= 2:
                apk_table = kampanye_tables[1]
                apk_rows = apk_table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header row
                apk_data = []
            
                for row in apk_rows:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    
                    # Ambil link maps dari iframe
                    maps_iframe = cols[-1].find_elements(By.TAG_NAME, "iframe")
                    maps_link = maps_iframe[0].get_attribute('src') if maps_iframe else "Data tidak ditemukan."
                    
                    # Ekstrak koordinat dari link (regex untuk mengekstrak angka setelah "marker=")
                    match = re.search(r"marker=(-?\d+\.\d+),(-?\d+\.\d+)", maps_link)
                    if match:
                        latitude = match.group(1)  # -7.885
                        longitude = match.group(2)  # 113.677
                        coordinates = f"{latitude},{longitude}"
                    else:
                        coordinates = "Data tidak ada."
            
                    # Buat baris data tanpa kolom iframe terakhir
                    row_data = [col.text for col in cols[:-1]]
                    row_data.append(coordinates)  # Tambahkan koordinat
                    apk_data.append(row_data)
            
                # Simpan ke CSV Laporan APK dengan nama yang berbeda berdasarkan index
                with open(os.path.join(subfolder_path, f"laporan_apk_calon_{index + 1}.csv"), "w", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow(["Tanggal pemasangan", "Jenis APK", "Jumlah Pemasangan", "Alamat Pemasangan", "Provinsi Pemasangan", "Kabupaten Pemasangan", "Koordinat"])
                    writer.writerows(apk_data)
            
                print(f"Data Laporan APK {index + 1} berhasil disimpan.")
            else:
                print(f"Tabel APK untuk kampanye ke-{index + 1} tidak ditemukan!")


            # Kembali ke halaman awal dengan driver.get
            driver.get('https://infopemilu.kpu.go.id/Pemilihan/Pasangan_calon')

            # Tunggu hingga halaman awal dimuat
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, 'filter-btn')))
            print("Kembali ke halaman awal.")


            # Pilih ulang jenis pemilihan dan wilayah
            jenis_pemilihan_select = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, 'jenis_pemilihan'))
            )
            time.sleep(5)
            jenis_pemilihan_select.click()
            driver.find_element(By.XPATH, f"//option[@value='{jenis_pemilihan}']").click()

            wilayah_select = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//span[@id='select2-wilayah-container']"))
            )
            wilayah_select.click()
            time.sleep(5)
            search_box = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//input[@class='select2-search__field']"))
            )
            search_box.send_keys(f"{provinsi}")
            time.sleep(2)
            option = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, f"//li[contains(@class, 'select2-results__option') and text()='{provinsi}']"))
            )
            option.click()

            # Klik tombol filter
            filter_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, 'filter-btn'))
            )
            filter_button.click()

            # Tunggu dan scroll halaman lagi
            time.sleep(5)
            driver.execute_script("window.scrollBy(0, window.innerHeight / 1);")
            time.sleep(5)


        # Ambil semua tombol kampanye di halaman awal
        dana_kampanye_buttons = driver.find_elements(By.XPATH, "//form[@action='Pasangan_calon/dana_kampanye']//button[@type='submit']")
        print(f"Jumlah tombol kampanye ditemukan: {len(dana_kampanye_buttons)}")

        for index in range(len(dana_kampanye_buttons)):
            # Refresh elemen tombol (karena DOM berubah setelah navigasi kembali)
            if index == 3 or index == 4:
                driver.execute_script("window.scrollBy(0, window.innerHeight / 1);")
                time.sleep(1)
                driver.execute_script("window.scrollBy(0, window.innerHeight / 2);")
                time.sleep(3)
            dana_kampanye_buttons = driver.find_elements(By.XPATH, "//form[@action='Pasangan_calon/dana_kampanye']//button[@type='submit']")
            dana_kampanye_buttons = dana_kampanye_buttons[index]
            subfolder_path = os.path.join(folder_path, f"Nomor {index + 1}")  # Nomor mulai dari 1
            if not os.path.exists(subfolder_path):
                os.makedirs(subfolder_path)  # Membuat folder untuk calon jika belum ada
            # Klik tombol kampanye
            dana_kampanye_buttons.click()

            # Tunggu hingga halaman kampanye dimuat
            time.sleep(20)
            
            # Debug: Scrape data dari halaman tujuan
            print(f"Scraping data dari tombol kampanye ke-{index + 1}")
            # Tambahkan logika scraping Anda di sini
           # Cari tabel yang ingin diambil datanya
            kampanye_table = driver.find_element(By.XPATH, "//table[@id='tbl_keanggotaan']")
            kampanye_rows = kampanye_table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header row
        
            kampanye_data = []
            for row in kampanye_rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                kampanye_data.append([col.text for col in cols])
        
            # Simpan data kampanye ke CSV
            if kampanye_data:
                filename = os.path.join(subfolder_path, f"TOTAL LAPORAN DANA KAMPANYE.csv")
                with open(filename, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Uraian", "LADK", "LPSDK", "LPPDK"])  # Header sesuai kolom tabel
                    writer.writerows(kampanye_data)
                print(f"Data laporan kampanye {index + 1} berhasil disimpan ke {filename}")

        
        # Inside the dana_kampanye_buttons loop, after clicking the button:
        
            # Temukan elemen tabel
            table_uang = driver.find_element(By.CSS_SELECTOR, "div#bentuk_uang table")
            
            # Ambil header tabel
            headers = []
            header_elements = table_uang.find_elements(By.CSS_SELECTOR, "thead th")
            for header in header_elements:
                headers.append(header.text.strip())
            
            # Ambil baris data
            rows = []
            row_elements = table_uang.find_elements(By.CSS_SELECTOR, "tbody tr")
            for row in row_elements:
                cells = []
                cell_elements = row.find_elements(By.CSS_SELECTOR, "td")
                for cell in cell_elements:
                    colspan = cell.get_attribute("colspan")
                    colspan = int(colspan) if colspan else 1
                    # Tambahkan nilai sel
                    cells.append(cell.text.strip())
                    # Tambahkan sel kosong untuk colspan jika ada
                    if colspan > 1:
                        cells.extend([''] * (colspan - 1))
                rows.append(cells)
            
            # Sesuaikan jumlah kolom setiap baris agar sama dengan header
            for row in rows:
                while len(row) < len(headers):
                    row.append('')
            
            # Simpan data ke CSV
            csv_file = os.path.join(subfolder_path,f"DETAIL LAPORAN DANA KAMPANYE DALAM BENTUK UANG.csv")
            with open(csv_file, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(headers)  # Tulis header
                writer.writerows(rows)  # Tulis baris data
            
            print(f"Data berhasil disimpan ke {csv_file}")


            # Cari tabel yang ingin diambil datanya
            # Tunggu hingga elemen tabel pertama "Bentuk Barang" muncul
            try:
                table_barang = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.col-sm-12.col-md-6.mt-2:nth-of-type(1) table"))
                )
            
                # Ambil header tabel
                headers_barang = [header.text.strip() for header in table_barang.find_elements(By.CSS_SELECTOR, "thead th")]
            
                # Ambil baris data
                rows_barang = []
                row_elements_barang = table_barang.find_elements(By.CSS_SELECTOR, "tbody tr")
                for row in row_elements_barang:
                    cells = []
                    cell_elements = row.find_elements(By.CSS_SELECTOR, "td")
                    for cell in cell_elements:
                        colspan = cell.get_attribute("colspan")
                        colspan = int(colspan) if colspan else 1
                        # Tambahkan nilai sel
                        cells.append(cell.text.strip())
                        # Tambahkan sel kosong untuk colspan jika ada
                        if colspan > 1:
                            cells.extend([''] * (colspan - 1))
                    rows_barang.append(cells)
            
                # Sesuaikan jumlah kolom setiap baris agar sama dengan header
                for row in rows_barang:
                    while len(row) < len(headers_barang):
                        row.append('')
            
                # Simpan data ke CSV untuk Tabel Barang
                csv_file_barang = os.path.join(subfolder_path,f"DETAIL LAPORAN DANA KAMPANYE DALAM BENTUK BARANG.csv")
                with open(csv_file_barang, "w", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow(headers_barang)  # Tulis header
                    writer.writerows(rows_barang)  # Tulis baris data
            
                print(f"Data tabel barang berhasil disimpan ke {csv_file_barang}")
            
            except Exception as e:
                print(f"Tabel Barang tidak ditemukan atau terjadi kesalahan: {e}")
            
            # Tunggu hingga elemen tabel kedua "Bentuk Jasa" muncul
            try:
                table_jasa = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.col-sm-12.col-md-6.mt-2:nth-of-type(2) table"))
                )
            
                # Ambil header tabel
                headers_jasa = [header.text.strip() for header in table_jasa.find_elements(By.CSS_SELECTOR, "thead th")]
            
                # Ambil baris data
                rows_jasa = []
                row_elements_jasa = table_jasa.find_elements(By.CSS_SELECTOR, "tbody tr")
                for row in row_elements_jasa:
                    cells = []
                    cell_elements = row.find_elements(By.CSS_SELECTOR, "td")
                    for cell in cell_elements:
                        colspan = cell.get_attribute("colspan")
                        colspan = int(colspan) if colspan else 1
                        # Tambahkan nilai sel
                        cells.append(cell.text.strip())
                        # Tambahkan sel kosong untuk colspan jika ada
                        if colspan > 1:
                            cells.extend([''] * (colspan - 1))
                    rows_jasa.append(cells)
            
                # Sesuaikan jumlah kolom setiap baris agar sama dengan header
                for row in rows_jasa:
                    while len(row) < len(headers_jasa):
                        row.append('')
            
                # Simpan data ke CSV untuk Tabel Jasa
                csv_file_jasa = os.path.join(subfolder_path,f"DETAIL LAPORAN DANA KAMPANYE DALAM BENTUK JASA Calon {index + 1}.csv")
                with open(csv_file_jasa, "w", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow(headers_jasa)  # Tulis header
                    writer.writerows(rows_jasa)  # Tulis baris data
            
                print(f"Data tabel jasa berhasil disimpan ke {csv_file_jasa}")
            
            except Exception as e:
                print(f"Tabel Jasa tidak ditemukan atau terjadi kesalahan: {e}")

            
            # # Menemukan elemen tabel dalam div dengan class tertentu
            table_laporan_harian = driver.find_element(By.XPATH, "//div[@class='col-sm-12 col-md-12 col-lg-12 mt-2']//table")
            
            # Ambil semua baris tabel (kecuali header)
            rows = table_laporan_harian.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header row
            
            # Menyimpan data yang akan di-scrape
            data = []
            for row in rows:
                # Ambil semua kolom dalam setiap baris
                cols = row.find_elements(By.TAG_NAME, "td")
                # Memastikan kolom data yang relevan
                if len(cols) > 0:
                    tanggal = cols[0].text.strip()  # Tanggal
                    bentuk = cols[1].text.strip()  # Bentuk
                    uang = cols[2].text.strip()  # Uang
                    barang = cols[3].text.strip()  # Barang
                    jasa = cols[4].text.strip()  # Jasa
                    total = cols[5].text.strip()  # Total
                    
                    # Menambahkan data dalam bentuk list
                    data.append([tanggal, bentuk, uang, barang, jasa, total])
            
            # Simpan data ke CSV
            if data:
                filename = os.path.join(subfolder_path,f"LAPORAN HARIAN.csv")
                with open(filename, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Tanggal", "Bentuk", "Uang(Rp)", "Barang(Rp)", "Jasa(Rp)", "Total(Rp)"])  # Header sesuai kolom tabel
                    writer.writerows(data)
                print(f"Data laporan harian berhasil disimpan ke {filename}")
            else:
                print("Tidak ada data untuk disimpan.")



            # Kembali ke halaman awal dengan driver.get
            driver.get('https://infopemilu.kpu.go.id/Pemilihan/Pasangan_calon')

            # Tunggu hingga halaman awal dimuat
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, 'filter-btn')))
            print("Kembali ke halaman awal.")


            # Pilih ulang jenis pemilihan dan wilayah
            jenis_pemilihan_select = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, 'jenis_pemilihan'))
            )
            time.sleep(5)
            jenis_pemilihan_select.click()
            driver.find_element(By.XPATH, f"//option[@value='{jenis_pemilihan}']").click()

            wilayah_select = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//span[@id='select2-wilayah-container']"))
            )
            wilayah_select.click()
            time.sleep(5)
            search_box = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//input[@class='select2-search__field']"))
            )
            search_box.send_keys(f"{provinsi}")
            time.sleep(2)
            option = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, f"//li[contains(@class, 'select2-results__option') and text()='{provinsi}']"))
            )
            option.click()

            # Klik tombol filter
            filter_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, 'filter-btn'))
            )
            filter_button.click()

            # Tunggu dan scroll halaman lagi
            time.sleep(5)
            driver.execute_script("window.scrollBy(0, window.innerHeight / 1);")
            time.sleep(5)

   
    

    except Exception as e:
        print(f"Terjadi kesalahan: {e}")


    finally:
        # Tutup browser
        driver.quit()

if __name__ == '__main__':
    scrape_kpu_data()
