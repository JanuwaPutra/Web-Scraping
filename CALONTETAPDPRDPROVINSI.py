from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time
import csv

# Setup Chrome Options
from selenium.webdriver.chrome.options import Options
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

# Setup driver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Tambahkan timeout dan pengaturan page load
driver.set_page_load_timeout(30)
driver.implicitly_wait(10)

def pilih_dapil_aceh_1(current_page=1):
    """Fungsi untuk memilih Dapil ACEH I dan konfigurasi entries"""
    try:
        wait = WebDriverWait(driver, 20)

        # Pilih 100 entries
        entries_select = wait.until(EC.presence_of_element_located((By.NAME, "tbl_ms_nasional_length")))
        entries_dropdown = Select(entries_select)
        entries_dropdown.select_by_value("100")
        time.sleep(1)  # Tunggu halaman memuat ulang
        
        # Pilih Dapil JAWA BARAT 5
        select_element = wait.until(EC.presence_of_element_located((By.ID, "filterDapil")))
        select = Select(select_element)
        select.select_by_visible_text("JAWA TIMUR 2")
        time.sleep(20)

        # Scroll ke bawah hingga mentok
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            # Scroll ke bawah
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)  # Tunggu agar halaman memuat data baru (jika ada)
            
            # Periksa apakah sudah mentok
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Navigasi ke halaman yang spesifik
        if current_page > 1:
            pagination_buttons = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@id='tbl_ms_nasional_paginate']/span/a")))
            
            # Cari tombol dengan page number yang benar
            for button in pagination_buttons:
                if button.text == str(current_page):
                    button.click()
                    time.sleep(10)  # Tunggu halaman memuat
                    break

    except Exception as e:
        print(f"Gagal memilih Dapil atau konfigurasi entries: {e}")
        raise

kandidat_data = []

try:
    driver.get("https://infopemilu.kpu.go.id/Pemilu/Dct_dprprov")
    
    # Mulai dari halaman pertama
    current_page = 1
    pilih_dapil_aceh_1(current_page)

    processed_kandidat = 0
    max_kandidat = 95
    
    while processed_kandidat < max_kandidat:
        try:
            rows = driver.find_elements(By.CSS_SELECTOR, "tr.odd, tr.even")
            
            # Jika kandidat yang diproses sudah mencapai 100, klik tombol Next
            if processed_kandidat >= 100:
                try:
                    next_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "tbl_ms_nasional_next"))
                    )
                    
                    # Periksa apakah tombol Next tidak disabled
                    if 'disabled' not in next_button.get_attribute('class'):
                        next_button.click()
                        current_page += 1  # Increment halaman
                        time.sleep(13)  # Tunggu halaman memuat
                        

                        processed_kandidat = 0
                    else:
                        # Jika tombol Next disabled, berarti sudah halaman terakhir
                        break
                except Exception as e:
                    print(f"Tidak dapat menemukan tombol Next atau mengkliknya: {e}")
                    break

            row = rows[processed_kandidat]

            try:
                profile_buttons = row.find_elements(By.CSS_SELECTOR, "input[value='PROFIL']")
                if profile_buttons:
                    driver.execute_script("arguments[0].click();", profile_buttons[0])
                    time.sleep(3)  # Tunggu halaman profil

                    data = {}
                    
                    # [Salin seluruh blok scraping data kandidat dari script sebelumnya]
                    # ... [paste your entire data scraping code here, just like in the previous script] ...

                    # ... [Rest of the scraping code remains the same] ...

                    try:
                                # Scrap data utama dari tabel
                            table = driver.find_element(By.CSS_SELECTOR, "div.col-md-8 table")

                            for tr in table.find_elements(By.TAG_NAME, "tr"):
                                    key = tr.find_element(By.TAG_NAME, "td").text.strip(":").replace(" ", "_").lower()
                                    value = tr.find_elements(By.TAG_NAME, "td")[1].text
                                    data[key] = value
                    except NoSuchElementException:
                                print(f"Data partai untuk kandidat ke-{processed_kandidat + 1} tidak ditemukan.")

                            # Scrap data partai
                    try:
                                partai_container = driver.find_element(By.XPATH, "//div[@class='col-md-12']//table/tbody/tr")
                                partai_name = partai_container.find_element(By.TAG_NAME, "h5").text
                                data['partai'] = partai_name
                    except NoSuchElementException:
                                print(f"Data partai untuk kandidat ke-{processed_kandidat + 1} tidak ditemukan.")


                            # Scrap nomor urut
                    try:
                                nomor_urut_container = driver.find_element(By.XPATH, "//div[@class='col-md-3']//center//h3")
                                nomor_urut = nomor_urut_container.text.strip()  # Mengambil nomor urut dan menghapus spasi ekstra
                                data['nomor_urut'] = nomor_urut
                    except NoSuchElementException:
                                print(f"Data nomor urut untuk kandidat ke-{processed_kandidat + 1} tidak ditemukan.")

                            # Scrap data alamat
                    try:
                                alamat_container = driver.find_element(By.XPATH, "//div[h3[text()='ALAMAT']]")
                                for li in alamat_container.find_elements(By.XPATH, ".//li[@class='list-group-item']"):
                                    try:
                                        key_element = li.find_element(By.TAG_NAME, "strong")
                                        key = key_element.text.strip(":").replace(" ", "_").lower()
                                        value = li.text.replace(key_element.text, "").strip(":").strip()
                                        data[key] = value
                                    except NoSuchElementException:
                                        continue
                    except NoSuchElementException:
                                print(f"Data alamat untuk kandidat ke-{processed_kandidat + 1} tidak ditemukan.")
    
                            # Scrap data pekerjaan
                    try:
                                pekerjaan_container = driver.find_element(By.XPATH, "//div[h3[text()='PEKERJAAN']]")
                                pekerjaan = pekerjaan_container.find_element(By.TAG_NAME, "p").text
                                data['pekerjaan'] = pekerjaan
                    except NoSuchElementException:
                                print(f"Data pekerjaan untuk kandidat ke-{processed_kandidat + 1} tidak ditemukan.")
    
                            # Scrap riwayat pekerjaan
                    try:
                                riwayat_pekerjaan_container = driver.find_element(By.XPATH, "//div[h3[text()='RIWAYAT PEKERJAAN']]")
                                riwayat_pekerjaan_data = []
                                for tr in riwayat_pekerjaan_container.find_elements(By.XPATH, ".//table/tbody/tr"):
                                    columns = tr.find_elements(By.TAG_NAME, "td")
                                    if len(columns) == 4:
                                        perusahaan = columns[0].text
                                        jabatan = columns[1].text
                                        tahun_masuk = columns[2].text
                                        tahun_keluar = columns[3].text
                                        riwayat_pekerjaan_data.append({
                                            'nama_perusahaan': perusahaan,
                                            'jabatan': jabatan,
                                            'tahun_masuk': tahun_masuk,
                                            'tahun_keluar': tahun_keluar
                                        })
                                data['riwayat_pekerjaan'] = riwayat_pekerjaan_data
                    except NoSuchElementException:
                                print(f"Data riwayat pekerjaan untuk kandidat ke-{processed_kandidat + 1} tidak ditemukan.")
    
                            # Scrap data status hukum
                    try:
                                status_hukum_container = driver.find_element(By.XPATH, "//div[h3[text()='STATUS HUKUM']]")
                                status_hukum = status_hukum_container.find_element(By.TAG_NAME, "p").text
                                data['status_hukum'] = status_hukum
                    except NoSuchElementException:
                                print(f"Data status hukum untuk kandidat ke-{processed_kandidat + 1} tidak ditemukan.")
    
                            # Scrap riwayat pendidikan
                    try:
                                riwayat_pendidikan_container = driver.find_element(By.XPATH, "//div[h3[text()='RIWAYAT PENDIDIKAN']]")
                                riwayat_pendidikan_data = []
                                for tr in riwayat_pendidikan_container.find_elements(By.XPATH, ".//table/tbody/tr"):
                                    columns = tr.find_elements(By.TAG_NAME, "td")
                                    if len(columns) == 4:
                                        jenjang_pendidikan = columns[0].text
                                        nama_institusi = columns[1].text
                                        tahun_masuk = columns[2].text
                                        tahun_keluar = columns[3].text
                                        riwayat_pendidikan_data.append({
                                            'jenjang_pendidikan': jenjang_pendidikan,
                                            'nama_institusi': nama_institusi,
                                            'tahun_masuk': tahun_masuk,
                                            'tahun_keluar': tahun_keluar
                                        })
                                data['riwayat_pendidikan'] = riwayat_pendidikan_data
                    except NoSuchElementException:
                                print(f"Data riwayat pendidikan untuk kandidat ke-{processed_kandidat + 1} tidak ditemukan.")
    
                            # Scrap riwayat kursus dan diklat
                    try:
                                riwayat_kursus_container = driver.find_element(By.XPATH, "//div[h3[text()='RIWAYAT KURSUS DAN DIKLAT']]")
                                riwayat_kursus_data = []
                                for tr in riwayat_kursus_container.find_elements(By.XPATH, ".//table/tbody/tr"):
                                    columns = tr.find_elements(By.TAG_NAME, "td")
                                    if len(columns) == 5:
                                        nama_kursus = columns[0].text
                                        lembaga_penyelenggara = columns[1].text
                                        nomor_sertifikat = columns[2].text
                                        tahun_masuk = columns[3].text
                                        tahun_keluar = columns[4].text
                                        riwayat_kursus_data.append({
                                            'nama_kursus': nama_kursus,
                                            'lembaga_penyelenggara': lembaga_penyelenggara,
                                            'nomor_sertifikat': nomor_sertifikat,
                                            'tahun_masuk': tahun_masuk,
                                            'tahun_keluar': tahun_keluar
                                        })
                                data['riwayat_kursus_diklat'] = riwayat_kursus_data 
                            
                    except NoSuchElementException:
                                print(f"Data riwayat kursus dan diklat untuk kandidat ke-{processed_kandidat + 1} tidak ditemukan.")

                            # Scrap riwayat organisasi
                    try:
                                riwayat_organisasi_container = driver.find_element(By.XPATH, "//div[h3[text()='RIWAYAT ORGANISASI']]")
                                riwayat_organisasi_data = []
                                for tr in riwayat_organisasi_container.find_elements(By.XPATH, ".//table/tbody/tr"):
                                    columns = tr.find_elements(By.TAG_NAME, "td")
                                    if len(columns) == 4:
                                        nama_organisasi = columns[0].text
                                        jabatan = columns[1].text
                                        tahun_masuk = columns[2].text
                                        tahun_keluar = columns[3].text
                                        riwayat_organisasi_data.append({
                                            'nama_organisasi': nama_organisasi,
                                            'jabatan': jabatan,
                                            'tahun_masuk': tahun_masuk,
                                            'tahun_keluar': tahun_keluar
                                        })
                                data['riwayat_organisasi'] = riwayat_organisasi_data
                    except NoSuchElementException:
                                print(f"Data riwayat organisasi untuk kandidat ke-{processed_kandidat + 1} tidak ditemukan.")

                            # Scrap riwayat penghargaan
                    try:
                                penghargaan_container = driver.find_element(By.XPATH, "//div[h3[text()='RIWAYAT PENGHARGAAN']]")
                                penghargaan_data = []
                                for tr in penghargaan_container.find_elements(By.XPATH, ".//table/tbody/tr"):
                                    columns = tr.find_elements(By.TAG_NAME, "td")
                                    if len(columns) == 3:
                                        nama_penghargaan = columns[0].text
                                        lembaga = columns[1].text
                                        tahun = columns[2].text
                                        penghargaan_data.append({
                                            'nama_penghargaan': nama_penghargaan,
                                            'lembaga': lembaga,
                                            'tahun': tahun
                                        })
                                data['riwayat_penghargaan'] = penghargaan_data
                    except NoSuchElementException:
                                print(f"Data riwayat penghargaan untuk kandidat ke-{processed_kandidat + 1} tidak ditemukan.")

                            # Scrap riwayat kursus dan diklat
                    try:
                                kursus_diklat_container = driver.find_element(By.XPATH, "//div[h3[text()='RIWAYAT KURSUS DAN DIKLAT']]")
                                kursus_diklat_data = []
                                for tr in kursus_diklat_container.find_elements(By.XPATH, ".//table/tbody/tr"):
                                    columns = tr.find_elements(By.TAG_NAME, "td")
                                    if len(columns) == 5:
                                        nama_kursus = columns[0].text
                                        lembaga_penyelenggara = columns[1].text
                                        nomor_sertifikat = columns[2].text
                                        tahun_masuk = columns[3].text
                                        tahun_keluar = columns[4].text
                                        kursus_diklat_data.append({
                                            'nama_kursus': nama_kursus,
                                            'lembaga_penyelenggara': lembaga_penyelenggara,
                                            'nomor_sertifikat': nomor_sertifikat,
                                            'tahun_masuk': tahun_masuk,
                                            'tahun_keluar': tahun_keluar
                                        })
                                data['riwayat_kursus_diklat'] = kursus_diklat_data
                    except NoSuchElementException:
                                print(f"Data riwayat kursus dan diklat untuk kandidat ke-{processed_kandidat + 1} tidak ditemukan.")

                            # Scrap data program usulan
                    try:
                                program_usulan_container = driver.find_element(By.XPATH, "//div[h3[text()='PROGRAM USULAN']]")
                                program_usulan = program_usulan_container.find_element(By.XPATH, ".//li[@class='list-group-item']//strong").text
                                data['program_usulan'] = program_usulan
                    except NoSuchElementException:
                                print(f"Data program usulan untuk kandidat ke-{processed_kandidat + 1} tidak ditemukan.")


                            # Scrap riwayat pasangan
                    try:
                                riwayat_pasangans_container = driver.find_element(By.XPATH, "//div[h3[text()='RIWAYAT PASANGAN']]")
                                riwayat_pasangans_data = []
                                for tr in riwayat_pasangans_container.find_elements(By.XPATH, ".//table/tbody/tr"):
                                    columns = tr.find_elements(By.TAG_NAME, "td")
                                    if len(columns) == 3:
                                        nama_pasangans = columns[0].text
                                        status_pasangans = columns[1].text
                                        jumlah_anaks = columns[2].text
                                        riwayat_pasangans_data.append({
                                            'nama_pasangans': nama_pasangans,
                                            'status_pasangans': status_pasangans,
                                            'jumlah_anaks': jumlah_anaks
                                        })
                                data['riwayat_pasangans'] = riwayat_pasangans_data
                    except NoSuchElementException:
                                print(f"Data riwayat pasangan untuk kandidat ke-{processed_kandidat + 1} tidak ditemukan.")


                    kandidat_data.append(data)
                    print(f"Kandidat di Halaman {current_page}, Kandidat ke-{processed_kandidat + 1}: {data}")

                    driver.back()
                    time.sleep(2)
                    
                    # Kembalikan ke halaman dengan nomor yang benar
                    pilih_dapil_aceh_1(current_page)

                    processed_kandidat += 1
                else:
                    print(f"Kandidat di Halaman {current_page}, Kandidat ke-{processed_kandidat + 1} tidak memiliki tombol profil aktif.")
                    processed_kandidat += 1

            except StaleElementReferenceException:
                driver.get("https://infopemilu.kpu.go.id/Pemilu/Dct_dprprov")
                pilih_dapil_aceh_1(current_page)
                continue

        except Exception as e:
            print(f"Gagal memproses kandidat di Halaman {current_page}, Kandidat ke-{processed_kandidat + 1}: {e}")
            driver.get("https://infopemilu.kpu.go.id/Pemilu/Dct_dprprov")
            pilih_dapil_aceh_1(current_page)
            continue

except Exception as e:
    print(f"Terjadi kesalahan utama: {e}")

finally:
    try:
        # Menentukan fieldnames secara dinamis
        fieldnames = set()
        for kandidat in kandidat_data:
            fieldnames.update(kandidat.keys())
        fieldnames = list(fieldnames)

        # Simpan ke CSV
        with open('JAWA TIMUR 2.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(kandidat_data)
        print("Data kandidat telah disimpan di csv")
    except Exception as e:
        print(f"Gagal menyimpan CSV: {e}")

    driver.quit()
