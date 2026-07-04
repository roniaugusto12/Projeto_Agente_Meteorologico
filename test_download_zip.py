import requests
import zipfile
import os

url = "https://portal.inmet.gov.br/uploads/dadoshistoricos/2026.zip"
zip_path = "2026.zip"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

try:
    if not os.path.exists(zip_path):
        print(f"Baixando arquivo historico de 47MB de: {url}...")
        r = requests.get(url, headers=headers, stream=True, timeout=30)
        r.raise_for_status()
        with open(zip_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print("Download concluido com sucesso!")
    else:
        print("Arquivo 2026.zip ja existe localmente.")

    # Abrir o ZIP e procurar pelo arquivo da estacao A301
    print("Lendo conteudo do arquivo ZIP...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        lista_arquivos = zip_ref.namelist()
        
        # Procurar por A301 ou RECIFE
        arquivos_recife = [f for f in lista_arquivos if "A301" in f or "RECIFE" in f]
        print(f"Arquivos encontrados para Recife: {arquivos_recife}")
        
except Exception as e:
    print(f"Erro: {e}")
