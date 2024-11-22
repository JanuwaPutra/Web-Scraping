import requests
import csv
from bs4 import BeautifulSoup


response = requests.get('https://id.wikipedia.org/wiki/Daftar_negara_menurut_benua')
# print(response.text)

soup = BeautifulSoup(response.text, 'html.parser')

for judul in soup.find_all('h1'):
    print(judul.text.strip())
    

with open('hasil_scraping.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['tes'])
    for judul in soup.find_all('h1' ):
        writer.writerow([judul.text.strip()])
