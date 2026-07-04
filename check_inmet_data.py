import requests

estacao = "A301"
datas = [
    "2023-01-15", "2023-06-15",
    "2024-01-15", "2024-06-15",
    "2025-01-15", "2025-06-15",
    "2026-01-15", "2026-05-15", "2026-06-15"
]

print("Consultando INMET para A301 em varias datas historicas:")
for d in datas:
    url = f"https://apitempo.inmet.gov.br/estacao/{d}/{d}/{estacao}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200 and len(r.text) > 2:
            print(f"OK - Data: {d} | Status: {r.status_code} | Registros: {len(r.json())}")
            break
        else:
            print(f"FAIL - Data: {d} | Status: {r.status_code} | Resposta: {r.text[:100]}")
    except Exception as e:
        print(f"ERR - Data: {d} | Erro: {e}")
