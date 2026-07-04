import logging
from sheets.google_sheets_client import ler_obras

logging.basicConfig(level=logging.INFO)

try:
    print("Tentando ler as obras da planilha...")
    obras = ler_obras()
    print("Obras lidas com sucesso:")
    print(obras)
except Exception as e:
    print("Erro durante a execução:")
    import traceback
    traceback.print_exc()
