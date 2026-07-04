import requests

estacoes = ["A301", "A341", "A357", "A309", "A322"]
data = "2026-07-02"

print(f"Consultando dados de {data} para várias estações:")
for e in estacoes:
    url = f"https://apitempo.inmet.gov.br/estacao/{data}/{data}/{e}"
    try:
        r = requests.get(url, timeout=10)
        print(f"Estação: {e} | Status: {r.status_code} | Tam. Resposta: {len(r.text)}")
        if r.status_code == 200:
            print(f"Exemplo de dados: {r.text[:200]}")
    except Exception as ex:
        print(f"Estação: {e} | Erro: {ex}")
