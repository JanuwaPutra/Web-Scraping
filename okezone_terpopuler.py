import requests
from bs4 import BeautifulSoup
import csv

# URL sumber
url = "https://www.okezone.com/"
response = requests.get(url)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    teks = soup.find_all('div', class_='grup-terp')

    data_terpopuler = []

    for item in teks:
        try:
            no = item.find('div', class_='no').get_text(strip=True)
            category = item.find('div', class_='desc-terp').find_all('a')[0].get_text(strip=True)
            title = item.find('div', class_='desc-terp').find_all('a')[1].get_text(strip=True)
            link = item.find('a', class_='img-terp')['href']

            image = item.find('img')['src']


            data_terpopuler.append({
                'Nomor': no,
                'Kategori': category,
                'Judul': title,
                'Link': link,
                'Gambar': image
            })
            
        except Exception as e:
            print(e)
    csv_file = 'terpopuler_okezone.csv'
    csv_columns = ['Nomor', 'Kategori', 'Judul', 'Link', 'Gambar']

    try:
        with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=csv_columns)
            writer.writeheader()
            writer.writerows(data_terpopuler)
        print(f"Data berhasil disimpan ke {csv_file}")
    except Exception as e:
        print(f"Terjadi kesalahan saat menyimpan ke CSV: {e}")
else:
    print(response.status_code)
