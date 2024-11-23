import requests
from bs4 import BeautifulSoup
import datetime as dt
import csv

# Tanggal hari ini
date = dt.date.today().strftime('%Y-%m-%d')

# URL target
url = f'https://indeks.kompas.com/?site=all&date={date}'

# Kirim permintaan GET ke URL
page = requests.get(url)
soup = BeautifulSoup(page.text, 'html.parser')

# List untuk menyimpan hasil scraping
article_results = []

# Cari semua artikel
articles = soup.find_all('div', class_='articleItem')

for article in articles:
    try:
        url = article.find('a', class_='article-link')['href']
        img = article.find('div', class_='articleItem-img').find('img')['src']
        title = article.find('h2', class_='articleTitle').text.strip()
        category = article.find('div', class_='articlePost-subtitle').text.strip()
        date = article.find('div', class_='articlePost-date').text.strip()

        # Ambil konten dari artikel
        cPage = requests.get(url)
        cSoup = BeautifulSoup(cPage.text, 'html.parser')
        content = cSoup.find('div', class_='read__content').text.strip()

        # Tambahkan hasil ke list
        article_results.append({
            'url': url,
            'img': img,
            'title': title,
            'category': category,
            'date': date,
            'content': content,
        })

    except Exception as e:
        print(f"Error scraping article: {e}")

# Tulis hasil ke file CSV
csv_file = 'article_results.csv'
try:
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        # Definisikan header CSV
        fieldnames = ['url', 'img', 'title', 'category', 'date', 'content']
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        # Tulis header
        writer.writeheader()

        # Tulis data
        writer.writerows(article_results)

    print(f"Hasil scraping berhasil disimpan ke {csv_file}")
except Exception as e:
    print(f"Error writing to CSV: {e}")
