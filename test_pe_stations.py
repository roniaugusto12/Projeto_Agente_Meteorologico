import requests

# As 12 estações automáticas/convencionais de PE
estacoes_pe = [
    "A301", "A309", "A322", "A329", "A341", "A349", 
    "A351", "A357", "A366", "A370"
]
data = "2026-07-03"  # ontem

print(f"Consultando dados de ontem ({data}) para estacoes de PE:")
for e in estacoes_pe:
    url = f"https://apitempo.inmet.gov.br/estacao/{data}/{data}/{e}"
    try:
        r = requests.get(url, timeout=10)
        print(f"Estacao: {e} | Status: {r.status_code} | Tam: {len(r.text)}")
        if r.status_code == 200 and len(r.text) > 2:
            print(f"  -> Sucesso! Encontrados {len(r.json())} registros.")
    except Exception as ex:
        print(f"Estacao: {e} | Erro: {ex}")
