import logging
import gspread
from sheets.google_sheets_client import _abrir_planilha

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def limpar_planilha():
    try:
        logger.info("Conectando à planilha para limpeza...")
        planilha = _abrir_planilha()
        aba = planilha.worksheet("OBRAS")
        
        # Obter todos os valores atuais
        valores = aba.get_all_values()
        if not valores:
            logger.info("A aba OBRAS está vazia.")
            return

        print(f"Estrutura atual: {len(valores)} linhas e {len(valores[0])} colunas.")

        # Limpar linhas iniciais completamente vazias
        while valores and all(celula == "" for celula in valores[0]):
            logger.info("Removendo linha 1 (completamente vazia)...")
            aba.delete_rows(1)
            valores = aba.get_all_values()

        # Limpar colunas iniciais completamente vazias
        if valores:
            coluna_vazia = True
            while coluna_vazia and valores and len(valores[0]) > 0:
                coluna_vazia = all(linha[0] == "" for linha in valores)
                if coluna_vazia:
                    logger.info("Removendo coluna A (completamente vazia)...")
                    aba.delete_columns(1)
                    valores = aba.get_all_values()
                else:
                    break

        # Padronizar o cabeçalho para coincidir exatamente com o esperado pelo código:
        # ID | Nome da Obra | Endereço | Bairro | CEP | Latitude | Longitude | Estação INMET | Status
        if valores:
            cabecalho_esperado = [
                "ID", "Nome da Obra", "Endereço", "Bairro", "CEP",
                "Latitude", "Longitude", "Estação INMET", "Status"
            ]
            
            # Atualiza o cabeçalho da primeira linha para ficar idêntico ao esperado
            aba.update("A1:I1", [cabecalho_esperado])
            logger.info("Cabeçalhos da aba OBRAS padronizados para:")
            logger.info(cabecalho_esperado)

        print("\n🧹 Limpeza da aba OBRAS concluída com sucesso!")

    except Exception as e:
        logger.error(f"Erro ao limpar planilha: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    limpar_planilha()
