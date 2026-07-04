import requests
from datetime import datetime, timedelta

estacao = "A301"
hoje = datetime(2026, 7, 3)

print("Consultando INMET para diferentes dias:")
for i in range(1, 10):
    data = (hoje - timedelta(days=i)).strftime("%Y-%m-%d")
    url = f"https://apitempo.inmet.gov.br/estacao/{data}/{data}/{estacao}"
    try:
        r = requests.get(url, timeout=10)
        print(f"Data: {data} | Status: {r.status_code} | Tam. Resposta: {len(r.text)} | Primeiros 100 char: {r.text[:100]}")
    except Exception as e:
        print(f"Data: {data} | Erro: {e}")
