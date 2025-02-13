import requests
from bs4 import BeautifulSoup

urls = [
    "https://startfacens.edmais.tech/"
]

# Cabeçalho com User-Agent para simular um navegador real
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
}

for url in urls:
    # Fazer a requisição com o cabeçalho
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # Criar um objeto BeautifulSoup para analisar o HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Extrair apenas o texto visível
        page_text = soup.get_text(separator="\n", strip=True)

        with open("./scraping/main_page.txt", "a") as file:
            file.write(page_text)

    else:
        print(f"Erro ao acessar o site {url}: \n{response.status_code}")
