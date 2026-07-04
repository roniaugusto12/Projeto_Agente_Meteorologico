import requests

estacao = "A301"
data = "2024-05-15"
url = f"https://apitempo.inmet.gov.br/estacao/{data}/{data}/{estacao}"

try:
    print(f"Consultando INMET para a data real {data}:")
    r = requests.get(url, timeout=15)
    print(f"Status: {r.status_code}")
    print(f"Tamanho da resposta: {len(r.text)}")
    if r.status_code == 200:
        dados = r.json()
        print(f"Total de registros: {len(dados)}")
        print("Primeiro registro:")
        print(dados[0])
except Exception as e:
    print(f"Erro: {e}")
