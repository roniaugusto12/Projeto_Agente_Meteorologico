import requests

url = "https://portal.inmet.gov.br/uploads/dadoshistoricos/2026.zip"
try:
    print(f"Verificando arquivo histórico de 2026: {url}")
    # Faz uma requisição HEAD para verificar se existe sem baixar tudo imediatamente
    r = requests.head(url, timeout=15)
    print(f"Status: {r.status_code}")
    print(f"Headers: {r.headers}")
except Exception as e:
    print(f"Erro: {e}")
