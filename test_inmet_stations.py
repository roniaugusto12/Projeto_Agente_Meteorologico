import requests

url = "https://apitempo.inmet.gov.br/estacoes/T"
try:
    r = requests.get(url, timeout=15)
    print(f"Status: {r.status_code}")
    estacoes = r.json()
    print(f"Total de estações encontradas: {len(estacoes)}")
    
    # Filtrar estações de Pernambuco (PE)
    pe_estacoes = [e for e in estacoes if e.get("SG_ESTADO") == "PE"]
    print(f"Total em PE: {len(pe_estacoes)}")
    
    # Procurar A301
    a301 = next((e for e in estacoes if e.get("CD_ESTACAO") == "A301"), None)
    if a301:
        print("Informações da estação A301:")
        print(a301)
    else:
        print("Estação A301 não encontrada na lista!")

    # Mostrar algumas estações de PE
    print("\nAlgumas estações automáticas em PE:")
    for e in pe_estacoes[:10]:
        print(f"- {e.get('CD_ESTACAO')}: {e.get('DC_NOME')} ({e.get('TP_ESTACAO')})")
        
except Exception as e:
    print(f"Erro: {e}")
