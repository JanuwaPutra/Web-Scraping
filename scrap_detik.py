import requests
from bs4 import BeautifulSoup
import datetime as dt

# Format tanggal sesuai kebutuhan (MM/DD/YYYY)
date = dt.date.today().strftime('%m/%d/%Y')

# URL awal dengan format parameter yang sesuai
base_url = f'https://news.detik.com/indeks?date={date}'

# Mengirim permintaan ke URL
page = requests.get(base_url)
soup = BeautifulSoup(page.text, 'html.parser')

# Menemukan semua elemen artikel
articles = soup.find_all('article', class_='list-content__item')

# Iterasi untuk mengambil judul artikel
for article in articles:
    try:
        # Mengambil judul dari elemen dengan class `media__title`
        title = article.find('h3', class_='media__title').text.strip()
        date_span = article.find('div', class_='media__date').find('span')
        publication_date = date_span['title'] if date_span else 'Tanggal tidak ditemukan'
        print(publication_date)
    except Exception as e:
        print(f"Error scraping article: {e}")
