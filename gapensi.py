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
    options.add_argument('--window-size=1920,1080')
    
    return webdriver.Chrome(options=options)

def get_company_detail(driver, company_link):
    try:
        # Klik link untuk membuka modal
        driver.execute_script("arguments[0].click();", company_link)
        time.sleep(1)
        
        # Tunggu modal muncul dan semua elemennya ter-load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "c-detail-text"))
        )
        
        # Ambil semua detail
        details = {}
        detail_list = driver.find_elements(By.CSS_SELECTOR, "ul.c-detail-text li")
        
        for item in detail_list:
            try:
                divs = item.find_elements(By.TAG_NAME, "div")
                if len(divs) >= 3:
                    label = divs[0].text.strip()
                    value = divs[2].text.strip()
                    
                    details[label] = value
            except:
                continue
        
        # Tunggu sebentar sebelum menutup modal
        time.sleep(1)
        
        # Tutup modal menggunakan JavaScript
        close_button = driver.find_element(By.CSS_SELECTOR, "button.close.c-modal__btn-close")
        driver.execute_script("arguments[0].click();", close_button)
        
        # Tunggu modal tertutup
        time.sleep(1)
        
        return details
        
    except Exception as e:
        print(f"Error getting company details: {str(e)}")
        return None

def get_table_data(driver):
    companies = []
    
    try:
        # Tunggu tabel muncul
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "c-table"))
        )
        
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
                    'no_registrasi': row.find_element(By.XPATH, ".//td[not(contains(@class, 'u-txt--center')) and not(contains(@class, 'u-txt--uppercase'))]").text.strip(),
                    'kualifikasi': row.find_element(By.XPATH, ".//td[contains(@class, 'u-txt--center')]").text
                }
                
                # Ambil detail dari modal
                details = get_company_detail(driver, company_link)
                if details:
                    company_data.update({
                        'nama_badan_usaha': details.get('Nama Badan Usaha', ''),
                        'nama_pimpinan_detail': details.get('Nama Pimpinan', ''),
                        'nomor_sertifikat': details.get('Nomor Sertifikat', ''),
                        'kualifikasi_detail': details.get('Kualifikasi', ''),
                        'tgl_kta': details.get('Tgl KTA', ''),
                        'email': details.get('Email', ''),
                        'alamat': details.get('Alamat', ''),
                        'kabupaten': details.get('Kabupaten Kota', ''),
                        'propinsi': details.get('Propinsi', '')
                    })
                
                companies.append(company_data)
                print(f"Successfully processed: {company_data['nama_perusahaan']}")
                
            except Exception as e:
                print(f"Error processing row: {str(e)}")
                continue
                
        return companies
            
    except Exception as e:
        print(f"Error in get_table_data: {str(e)}")
        return []


def save_to_csv(data, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'No', 'Nama Perusahaan', 'Pimpinan', 'No Registrasi', 'Kualifikasi',
            'Nama Badan Usaha', 'Nama Pimpinan (Detail)', 'Nomor Sertifikat', 
            'Kualifikasi Detail', 'Tgl KTA', 'Email', 'Alamat', 'Kabupaten', 'Propinsi'
        ])
        
        for company in data:
            writer.writerow([
                company.get('no', ''),
                company.get('nama_perusahaan', ''),
                company.get('pimpinan', ''),
                company.get('no_registrasi', ''),
                company.get('kualifikasi', ''),
                company.get('nama_badan_usaha', ''),
                company.get('nama_pimpinan_detail', ''),
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
    base_url = "https://gapensi.or.id/anggota?limit=50&keyword=&idkual=&subkla=&kab=&char=&tahun=2018&provinsi=35&page=1"
    all_companies = []
    page = 1
    
    try:
        while True:
            print(f"\nScraping page {page}")
            url = f"{base_url}&page={page}" if page > 1 else base_url
            driver.get(url)
            
            # Tunggu halaman dimuat
            time.sleep(1)
            
            # Ambil data dari tabel
            companies = get_table_data(driver)
            if companies:
                all_companies.extend(companies)
                print(f"Berhasil mengambil {len(companies)} data dari halaman {page}")
            else:
                print(f"Tidak ada data pada halaman {page}")
            
            # Cek halaman selanjutnya
            try:
                next_buttons = driver.find_elements(By.XPATH, "//a[contains(@href, 'page=') and not(contains(@class, 'active'))]")
                if not next_buttons or page >= 63:  # Batasi sampai halaman 31 sesuai pagination
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
        save_to_csv(all_companies, 'tes.csv')
        print(f"\nScraping selesai! {len(all_companies)} perusahaan telah disimpan ke gapensi_data.csv")
    else:
        print("Tidak ada data yang berhasil di-scrape")

if __name__ == "__main__":
    main()
