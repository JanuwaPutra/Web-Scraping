import requests
from bs4 import BeautifulSoup

url = "https://www.worldometers.info/coronavirus/"
response = requests.get(url)

soup = BeautifulSoup(response.text, 'html.parser')
teks = soup.find_all(id = 'maincounter-wrap')
for x in teks :
    print(x.text)
