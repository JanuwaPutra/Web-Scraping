from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import csv
import time

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    return webdriver.Chrome(options=options)

def get_company_detail(driver, company_link):
    try:
        # Klik link untuk membuka modal
        driver.execute_script("arguments[0].click();", company_link)
        time.sleep(1)
        
        # Tunggu modal muncul
        modal = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "c-modal__body"))
        )
        
        # Ambil semua list item dari detail
        detail_items = modal.find_elements(By.CSS_SELECTOR, "ul.c-detail-text li")
        details = {}
        
        # Mapping label ke key yang akan digunakan
        label_mapping = {
            'Nama Badan Usaha': 'nama_badan_usaha',
            'Nama Pimpinan': 'nama_pimpinan',
            'Nomor Sertifikat': 'nomor_sertifikat',
            'Kualifikasi': 'kualifikasi_detail',
            'Tgl KTA': 'tgl_kta',
            'Email': 'email',
            'Alamat': 'alamat',
            'Kabupaten Kota': 'kabupaten',
            'Propinsi': 'propinsi'
        }
        
        for item in detail_items:
            try:
                label = item.find_element(By.XPATH, ".//div[1]").text.strip()
                value = item.find_element(By.XPATH, ".//div[3]").text.strip()
                
                if label in label_mapping:
                    details[label_mapping[label]] = value
            except:
                continue
        
        # Tutup modal
        close_button = driver.find_element(By.CSS_SELECTOR, "button.c-modal__btn-close")
        driver.execute_script("arguments[0].click();", close_button)
        time.sleep(0.5)
        
        return details
        
    except Exception as e:
        print(f"Error getting company details: {str(e)}")
        return None

def get_table_data(driver):
    companies = []
    
    # Tunggu sampai tabel muncul
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "c-table"))
        )
        
        # Tunggu rows muncul
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//tbody[@id='accordion']/tr[contains(@id, 'heading_')]"))
        )
    except TimeoutException:
        print("Timeout waiting for table to load")
        return companies
    
    # Ambil semua baris data
    rows = driver.find_elements(By.XPATH, "//tbody[@id='accordion']/tr[contains(@id, 'heading_')]")
    
    for row in rows:
        try:
            # Ambil link perusahaan untuk detail
            company_link = row.find_element(By.XPATH, ".//td[contains(@class, 'u-txt--uppercase')]/a")
            
            # Ambil data utama perusahaan
            company_data = {
                'no': row.find_element(By.XPATH, ".//th[@scope='row']").text,
                'nama_perusahaan': company_link.text,
                'pimpinan': row.find_elements(By.XPATH, ".//td[contains(@class, 'u-txt--uppercase')]")[1].text,
                'no_registrasi': row.find_element(By.XPATH, ".//td[not(contains(@class, 'u-txt--center'))][2]").text,
                'kualifikasi': row.find_element(By.XPATH, ".//td[contains(@class, 'u-txt--center')]").text
            }
            
            # Ambil detail perusahaan dari modal
            details = get_company_detail(driver, company_link)
            if details:
                company_data.update(details)
            
            companies.append(company_data)
            print(f"Successfully processed: {company_data['nama_perusahaan']}")
            
        except Exception as e:
            print(f"Error processing row: {str(e)}")
            continue
            
    return companies

def save_to_csv(data, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'No', 'Nama Perusahaan', 'Pimpinan', 'No Registrasi', 'Kualifikasi',
            'Nama Badan Usaha', 'Nama Pimpinan', 'Nomor Sertifikat', 'Kualifikasi Detail',
            'Tgl KTA', 'Email', 'Alamat', 'Kabupaten', 'Propinsi'
        ])
        
        for company in data:
            writer.writerow([
                company.get('no', ''),
                company.get('nama_perusahaan', ''),
                company.get('pimpinan', ''),
                company.get('no_registrasi', ''),
                company.get('kualifikasi', ''),
                company.get('nama_badan_usaha', ''),
                company.get('nama_pimpinan', ''),
                company.get('nomor_sertifikat', ''),
                company.get('kualifikasi_detail', ''),
                company.get('tgl_kta', ''),
                company.get('email', ''),
                company.get('alamat', ''),
                company.get('kabupaten', ''),
                company.get('propinsi', '')
            ])

def main():
    driver = setup_driver()
    base_url = "https://gapensi.or.id/anggota?limit=50&tahun=2024&provinsi=35&kab=&idkual=&subkla=&keyword="
    all_companies = []
    page = 1
    
    try:
        while True:
            print(f"\nScraping page {page}")
            url = f"{base_url}&page={page}" if page > 1 else base_url
            driver.get(url)
            
            # Tunggu halaman dimuat
            time.sleep(3)
            
            # Ambil data dari tabel
            companies = get_table_data(driver)
            if companies:
                all_companies.extend(companies)
            else:
                print(f"No data found on page {page}")
            
            # Cek halaman selanjutnya
            try:
                next_buttons = driver.find_elements(By.XPATH, "//a[contains(@href, 'page=') and not(contains(@class, 'active'))]")
                if not next_buttons or page >= 31:  # Batasi sampai halaman 31 sesuai pagination
                    break
                page += 1
            except NoSuchElementException:
                break
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()
        
    # Simpan data ke CSV
    if all_companies:
        save_to_csv(all_companies, 'gapensi_data.csv')
        print(f"\nScraping selesai! {len(all_companies)} perusahaan telah disimpan ke gapensi_data.csv")
    else:
        print("Tidak ada data yang berhasil di-scrape")

if __name__ == "__main__":
    main()
