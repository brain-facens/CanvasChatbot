import requests
from bs4 import BeautifulSoup

# URL do site
url = "https://startfacens.edmais.tech/docs/acesso-ao-forum/"

# Cabeçalho com User-Agent para simular um navegador real
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
}

# Fazer a requisição com o cabeçalho
response = requests.get(url, headers=headers)

if response.status_code == 200:
    # Criar um objeto BeautifulSoup para analisar o HTML
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Extrair apenas o texto visível
    page_text = soup.get_text(separator="\n", strip=True)

    with open("acesso_forum.txt", "w") as file:
        file.write(page_text)
    
    #print(page_text)
else:
    print(f"Erro ao acessar o site: {response.status_code}")
