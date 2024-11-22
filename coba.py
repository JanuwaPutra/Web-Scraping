import requests
response = requests.get('https://revou.co/panduan-teknis/web-scraping-python')
print(response.text)

from bs4 import BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')

for judul in soup.find_all('h2'):
    print(judul.text.strip())
    
    import csv
with open('hasil_scraping.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Judul'])
    for judul in soup.find_all('h2'):
        writer.writerow([judul.text.strip()])