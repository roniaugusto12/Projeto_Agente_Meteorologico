import zipfile
import csv
import io
import logging
from datetime import datetime
import gspread

# Reutilizar lógica de classificação e conexão com planilhas
from coletor.inmet_client import classificar_dia
from sheets.google_sheets_client import _abrir_planilha, ABA_REGISTROS, ler_obras

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

zip_path = "2026.zip"
csv_name = "INMET_NE_PE_A301_RECIFE_01-01-2026_A_30-06-2026.CSV"

def converter_valor_csv(val: str) -> float | None:
    """Converte valores decimais do padrão brasileiro (com vírgula) para float."""
    val = val.strip()
    if not val or val == "null" or val == "-9999":
        return None
    try:
        return float(val.replace(",", "."))
    except ValueError:
        return None

def formatar_para_sheet(val) -> str:
    """Formata valores numéricos para escrita no Google Sheets brasileiro (ponto por vírgula)."""
    if val is None:
        return ""
    return str(val).replace(".", ",")

def processar_e_importar():
    try:
        # 1. Obter a obra ativa de Recife da planilha para pegar ID e Nome
        logger.info("Lendo obras da planilha...")
        obras = ler_obras()
        if not obras:
            logger.error("Nenhuma obra ativa encontrada para vincular os registros!")
            return
            
        # Pegamos a primeira obra de Recife (que usa estação A301)
        obra_recife = next((o for o in obras if o.get("Estação INMET") == "A301" or o.get("ID") == 1), obras[0])
        id_obra = obra_recife.get("ID", 1)
        nome_obra = obra_recife.get("Nome da Obra", "Edf. Porto Paraíso")
        logger.info(f"Registros serão vinculados à obra: {nome_obra} (ID: {id_obra})")

        # 2. Abrir o arquivo ZIP e extrair a planilha de Recife
        logger.info(f"Lendo dados históricos do arquivo {zip_path}...")
        dados_por_data = {}
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            with zip_ref.open(csv_name) as f:
                # Decodifica o conteúdo em tempo de leitura
                text_stream = io.TextIOWrapper(f, encoding='iso-8859-1')
                reader = csv.reader(text_stream, delimiter=';')
                
                # Pular metadados (primeiras 8 linhas)
                for _ in range(8):
                    next(reader)
                
                # Ler cabeçalho (linha 9)
                headers = next(reader)
                
                # Mapeamento de colunas baseado na linha 9 impressa
                # 0: Data, 1: Hora UTC, 2: Precipitação, 9: Temp Max, 10: Temp Min, 13: Umidade Max, 17: Rajada, 18: Velocidade Vento
                for row in reader:
                    if not row or len(row) < 19:
                        continue
                    
                    data_raw = row[0].replace("/", "-")  # e.g., "2026-04-15"
                    
                    # Filtrar apenas Abril (04) e Maio (05) de 2026
                    if not (data_raw.startswith("2026-04-") or data_raw.startswith("2026-05-")):
                        continue
                    
                    hora_raw = row[1].split()[0]  # "1200 UTC" -> "1200"
                    
                    # Cria o dicionário simulando a estrutura da API INMET
                    registro_hora = {
                        "DT_MEDIDA": data_raw,
                        "HR_MEDIDA": hora_raw,
                        "CHUVA": converter_valor_csv(row[2]),
                        "TEM_MAX": converter_valor_csv(row[9]),
                        "TEM_MIN": converter_valor_csv(row[10]),
                        "UMD_MAX": converter_valor_csv(row[13]),
                        "VEN_RAJ": converter_valor_csv(row[17]),
                        "VEN_VEL": converter_valor_csv(row[18]),
                    }
                    
                    if data_raw not in dados_por_data:
                        dados_por_data[data_raw] = []
                    dados_por_data[data_raw].append(registro_hora)

        logger.info(f"Processamento concluído. Encontrados dados para {len(dados_por_data)} dias.")

        # 3. Conectar ao Google Sheets
        logger.info("Conectando ao Google Sheets...")
        planilha = _abrir_planilha()
        aba_reg = planilha.worksheet(ABA_REGISTROS)
        
        # Obter datas que já estão na planilha para evitar duplicados
        valores_existentes = aba_reg.get_all_values()
        datas_existentes = set()
        if len(valores_existentes) > 1:
            for linha in valores_existentes[1:]:
                # Coluna 0: Data, Coluna 1: ID Obra
                if len(linha) > 1 and str(linha[1]) == str(id_obra):
                    datas_existentes.add(linha[0])

        novas_linhas = []
        
        # Ordenar as datas para gravar cronologicamente
        for data_str in sorted(dados_por_data.keys()):
            if data_str in datas_existentes:
                logger.info(f"Dia {data_str} já registrado para a obra {id_obra}. Pulando.")
                continue
                
            registros_dia = dados_por_data[data_str]
            
            # Executar a classificação baseada na lógica v2.1
            classificacao, observacoes = classificar_dia(registros_dia, data_str)
            
            # Calcular agregações diárias
            chuvas = [r["CHUVA"] for r in registros_dia if r["CHUVA"] is not None]
            ven_vel = [r["VEN_VEL"] for r in registros_dia if r["VEN_VEL"] is not None]
            ven_raj = [r["VEN_RAJ"] for r in registros_dia if r["VEN_RAJ"] is not None]
            umd_max = [r["UMD_MAX"] for r in registros_dia if r["UMD_MAX"] is not None]
            tem_max = [r["TEM_MAX"] for r in registros_dia if r["TEM_MAX"] is not None]
            tem_min = [r["TEM_MIN"] for r in registros_dia if r["TEM_MIN"] is not None]
            
            chuva_total = sum(chuvas) if chuvas else 0.0
            vento_max = max(ven_vel) if ven_vel else None
            rajada_max = max(ven_raj) if ven_raj else None
            umidade_max = max(umd_max) if umd_max else None
            temp_max = max(tem_max) if tem_max else None
            temp_min = min(tem_min) if tem_min else None
            
            # Montar a linha para o Sheets
            linha_dados = [
                data_str,
                id_obra,
                nome_obra,
                formatar_para_sheet(round(chuva_total, 2)),
                formatar_para_sheet(vento_max),
                formatar_para_sheet(rajada_max),
                formatar_para_sheet(umidade_max),
                formatar_para_sheet(temp_max),
                formatar_para_sheet(temp_min),
                "INMET (Histórico)",
                classificacao,
                observacoes
            ]
            novas_linhas.append(linha_dados)
            
        # 4. Gravar os dados em lote no Sheets
        if novas_linhas:
            logger.info(f"Gravando {len(novas_linhas)} registros no Google Sheets...")
            aba_reg.append_rows(novas_linhas)
            logger.info("Registros gravados com sucesso!")
        else:
            logger.info("Nenhum novo registro para gravar.")

        print(f"\n🚀 Sucesso! Processados e gravados {len(novas_linhas)} dias de Abril e Maio de 2026 para a obra {nome_obra}!")

    except Exception as e:
        logger.error(f"Erro no processamento/gravação: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    processar_e_importar()
