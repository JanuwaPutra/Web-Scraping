import requests
from bs4 import BeautifulSoup
import csv
import time

def scrape_page(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    return soup


with open('detik_articles.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    
    writer.writerow(['Title', 'Publication Date', 'Content'])

    base_url = "https://news.detik.com/indeks?date=11/26/2024"  
    current_url = base_url

    while current_url:
        print(f"Scraping page: {current_url}")
        soup = scrape_page(current_url)

        articles = soup.find_all('article', class_='list-content__item')
        
        for article in articles:
            try:
                url = article.find('a', class_='media__link')['href']
                
                title = article.find('h3', class_='media__title').text.strip()
                
                date_span = article.find('div', class_='media__date').find('span')
                publication_date = date_span['title'] if date_span else 'Tanggal tidak ditemukan'

                cPage = requests.get(url)
                cSoup = BeautifulSoup(cPage.text, 'html.parser')
                
                content = cSoup.find('div', class_='detail__body-text itp_bodycontent')
                
                if content:
                    for ad in content.find_all('div', class_='ads-scrollpage-container'):
                        ad.decompose()

                    article_text = content.get_text(separator=' ', strip=True)

                    writer.writerow([title, publication_date, article_text])
                    print(f"Article '{title}' has been written to CSV.")

            except Exception as e:
                print(f"Error scraping article: {e}")
        
        next_button = soup.find('a', class_='pagination__item', text='Next')
        if next_button:
            current_url = next_button['href']
        else:
            print("No next page found. Stopping.")
            current_url = None
        
        time.sleep(2) 
