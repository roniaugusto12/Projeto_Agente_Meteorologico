import logging
from sheets.google_sheets_client import _abrir_planilha, ABA_REGISTROS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def limpar_dias_produtivos():
    try:
        logger.info("Conectando ao Google Sheets...")
        planilha = _abrir_planilha()
        aba_reg = planilha.worksheet(ABA_REGISTROS)
        
        logger.info("Lendo todos os registros existentes...")
        linhas = aba_reg.get_all_values()
        
        if not linhas:
            logger.info("Planilha vazia.")
            return
            
        header = linhas[0]
        registros = linhas[1:]
        
        # Filtrar registros removendo os classificados como "PRODUTIVO"
        registros_filtrados = []
        removidos = 0
        
        for r in registros:
            # A coluna "Classificação" é a coluna K (índice 10)
            if len(r) > 10 and r[10] == "PRODUTIVO":
                removidos += 1
            else:
                registros_filtrados.append(r)
                
        logger.info(f"Encontrados {len(registros)} registros. Removendo {removidos} registros PRODUTIVO.")
        
        # Reescrever a planilha
        logger.info("Limpando a aba e regravando os dados filtrados...")
        aba_reg.clear()
        
        novos_dados = [header] + registros_filtrados
        aba_reg.update('A1', novos_dados)
        
        logger.info("Limpeza concluída com sucesso!")
        print(f"\n✅ Sucesso! Removidos {removidos} registros com classificação 'PRODUTIVO' da planilha.")
        
    except Exception as e:
        logger.error(f"Erro ao limpar dias produtivos: {e}")

if __name__ == "__main__":
    limpar_dias_produtivos()
