import requests

estacao = "A301"
# Testar datas em meses anteriores
datas = ["2026-06-15", "2026-05-15", "2026-04-15", "2026-01-15", "2025-07-15"]

print("Consultando INMET para datas passadas:")
for data in datas:
    url = f"https://apitempo.inmet.gov.br/estacao/{data}/{data}/{estacao}"
    try:
        r = requests.get(url, timeout=10)
        print(f"Data: {data} | Status: {r.status_code} | Tam. Resposta: {len(r.text)}")
        if r.status_code == 200 and len(r.text) > 0:
            print(f"Sucesso! Registros: {len(r.json())}")
            break
    except Exception as e:
        print(f"Data: {data} | Erro: {e}")
