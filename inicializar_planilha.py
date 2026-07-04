import logging
import gspread
from sheets.google_sheets_client import _abrir_planilha

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

def inicializar():
    try:
        logger.info("Conectando à planilha...")
        planilha = _abrir_planilha()
        logger.info(f"Conectado com sucesso à planilha: '{planilha.title}' (ID: {planilha.id})")
        
        # 1. Obter ou criar a aba OBRAS
        try:
            aba_obras = planilha.worksheet("OBRAS")
            logger.info("Aba 'OBRAS' já existe.")
        except gspread.WorksheetNotFound:
            # Tenta renomear a aba padrão do Google Sheets (geralmente Página1 ou Sheet1)
            worksheets = planilha.worksheets()
            if len(worksheets) == 1 and worksheets[0].title in ["Página1", "Página 1", "Sheet1", "Sheet 1"]:
                sheet_padrao = worksheets[0]
                sheet_padrao.update_title("OBRAS")
                aba_obras = sheet_padrao
                logger.info(f"Aba padrão '{sheet_padrao.title}' renomeada para 'OBRAS'.")
            else:
                aba_obras = planilha.add_worksheet(title="OBRAS", rows=1000, cols=10)
                logger.info("Aba 'OBRAS' criada.")

        # Configurar cabeçalho da aba OBRAS
        cabecalho_obras = [
            "ID", "Nome da Obra", "Endereço", "Bairro", "CEP",
            "Latitude", "Longitude", "Estação INMET", "Status"
        ]
        
        # Verifica se a aba está vazia
        valores_obras = aba_obras.get_all_values()
        if not valores_obras:
            aba_obras.append_row(cabecalho_obras)
            logger.info("Cabeçalho da aba OBRAS inserido.")
            # Insere uma obra exemplo ativa
            obra_exemplo = [
                "1",
                "Obra Teste Fachada",
                "Av. Boa Viagem, 1000",
                "Boa Viagem",
                "51011-000",
                "-8.123",
                "-34.900",
                "A301",
                "ATIVO"
            ]
            aba_obras.append_row(obra_exemplo)
            logger.info("Obra de exemplo ativa inserida na aba OBRAS.")
        else:
            logger.info("Aba OBRAS já contém dados.")

        # 2. Obter ou criar a aba REGISTROS_METEOROLOGICOS
        try:
            aba_reg = planilha.worksheet("REGISTROS_METEOROLOGICOS")
            logger.info("Aba 'REGISTROS_METEOROLOGICOS' já existe.")
        except gspread.WorksheetNotFound:
            aba_reg = planilha.add_worksheet(title="REGISTROS_METEOROLOGICOS", rows=10000, cols=12)
            logger.info("Aba 'REGISTROS_METEOROLOGICOS' criada.")

        # Configurar cabeçalho da aba REGISTROS_METEOROLOGICOS
        cabecalho_reg = [
            "Data", "ID Obra", "Nome da Obra", "Precip. (mm)",
            "Vento Máx (m/s)", "Rajada (m/s)", "Umidade Máx (%)",
            "Temp. Máx (°C)", "Temp. Mín (°C)", "Fonte", "Classificação", "Observações"
        ]
        
        valores_reg = aba_reg.get_all_values()
        if not valores_reg:
            aba_reg.append_row(cabecalho_reg)
            logger.info("Cabeçalho da aba REGISTROS_METEOROLOGICOS inserido.")
        else:
            logger.info("Aba REGISTROS_METEOROLOGICOS já contém dados.")

        print("\n🎉 Planilha inicializada com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro ao inicializar planilha: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inicializar()
