import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#! vs__search (input)
#! vs__dropdown-option 

# ? Save Image
    # Buat folder Kelurahan
# ? Save Image
def save_image(url, kelurahan, tps, save_path):
    # Buat folder Kelurahan
    kelurahan_folder = os.path.join("hasil", kelurahan)
    # Buat subfolder TPS di dalam folder Kelurahan
    tps_folder = os.path.join(kelurahan_folder, tps)
    os.makedirs(tps_folder, exist_ok=True)  # Buat folder jika belum ada

    # Gabungkan path folder dengan nama file
    file_path = os.path.join(tps_folder, save_path)

    # Simpan gambar
    response = requests.get(url)
    if response.status_code == 200:
        with open(file_path, 'wb') as f:
            f.write(response.content)
            print("Gambar Berhasil disimpan:", file_path)
    else:
        print("Gambar gagal disimpan:", file_path)




# ? Get image url
def get_image_urls():
    elements = driver.find_elements(By.XPATH, '//div[@class="col-md-4"]')
    image_urls = [element.find_element(By.TAG_NAME, 'img').get_attribute('src') for element in elements]
    return image_urls

# ? Untuk Cari dropdown option
def get_dropdown_option_tps():
    input_element = driver.find_element(By.XPATH, '(//input[@class="vs__search"])[7]')
    input_element.click()
    time.sleep(1)
    
    options = driver.find_elements(By.CSS_SELECTOR, '.vs__dropdown-option')
    print(len(options))
    
    data = [option.text for option in options]
    return data

def get_dropdown_option_kelurahan():
    input_element = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, '//input[contains(@placeholder, "Pilih Kelurahan")]'))
    )
    input_element.click()
    time.sleep(1)
    
    options = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.vs__dropdown-option'))
    )
    data = [option.text for option in options]
    return data


# ? Untuk klik dropdown option dan masukkan value lalu di enter
def click_and_input_tps(option):
    input_element = driver.find_element(By.XPATH, '(//input[@class="vs__search"])[7]')
    input_element.clear()
    
    input_element.send_keys(option)
    input_element.send_keys(Keys.RETURN)
    
    time.sleep(1)

def click_and_input_kelurahan(option):
    input_element = driver.find_element(By.XPATH, '(//input[@class="vs__search"])[6]')
    input_element.clear()
    
    input_element.send_keys(option)
    input_element.send_keys(Keys.RETURN)
    
    time.sleep(1)

if __name__ == "__main__":
    starting_url= "https://pemilu2024.kpu.go.id/pilpres/hitung-suara/31/3101/310102"
    driver = webdriver.Chrome()
    driver.get(starting_url)

    #! PROVINSI-KABUPATEN-KECAMATAN-KELURAHAN-TPS 000
    
    provinsi = "JAKARTA"
    kabupaten = "ADM. KEP. SERIBU"
    kecamatan = "KEPULAUAN SERIBU SELATAN"
    
    possible_kelurahan = get_dropdown_option_kelurahan()
    
    for kelurahan in possible_kelurahan:
        click_and_input_kelurahan(kelurahan)
        possible_tps = get_dropdown_option_tps()
    
        for tps in possible_tps:
            click_and_input_tps(tps)
            image_urls = get_image_urls()
    
            # Simpan semua gambar yang ditemukan
            for idx, image_url in enumerate(image_urls):
                if image_url:
                    save_path = f"{provinsi}-{kabupaten}-{kecamatan}-{tps}-{idx+1}.jpg"
                    save_image(image_url, kelurahan, tps, save_path)


        
    driver.quit()
