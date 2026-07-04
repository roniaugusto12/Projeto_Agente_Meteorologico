import logging
import gspread
from collections import Counter
from sheets.google_sheets_client import _abrir_planilha

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def gerar_dashboard():
    try:
        logger.info("Conectando à planilha...")
        planilha = _abrir_planilha()
        
        # 1. Ler dados
        try:
            aba_reg = planilha.worksheet("REGISTROS_METEOROLOGICOS")
        except gspread.WorksheetNotFound:
            logger.error("Aba 'REGISTROS_METEOROLOGICOS' não encontrada.")
            return

        registros = aba_reg.get_all_values()
        if len(registros) <= 1:
            logger.warning("Nenhum registro meteorológico encontrado.")
            return

        # Cabeçalho está na linha 0. A classificação é a penúltima ou coluna 10 (K).
        # Vamos encontrar o índice da coluna "Classificação".
        cabecalho = registros[0]
        try:
            idx_classificacao = cabecalho.index("Classificação")
        except ValueError:
            logger.error("Coluna 'Classificação' não encontrada.")
            return

        # Extrair e contar as classificações
        classificacoes = [linha[idx_classificacao] for linha in registros[1:] if len(linha) > idx_classificacao]
        contagem = Counter(classificacoes)

        # 2. Obter ou criar aba DASHBOARD
        try:
            aba_dash = planilha.worksheet("DASHBOARD")
            logger.info("Aba 'DASHBOARD' encontrada, atualizando...")
            aba_dash.clear()
        except gspread.WorksheetNotFound:
            aba_dash = planilha.add_worksheet(title="DASHBOARD", rows=100, cols=10)
            logger.info("Aba 'DASHBOARD' criada.")

        # 3. Preparar e inserir dados
        dados_inserir = [
            ["Resumo de Status das Obras"],
            ["Classificação", "Total de Dias"]
        ]
        
        ordem_exibicao = ["IMPRODUTIVO_TOTAL", "IMPRODUTIVO_PARCIAL", "PRODUTIVO_RESSALVA", "PRODUTIVO", "PENDENTE"]
        cores = {
            "IMPRODUTIVO_TOTAL": {"red": 0.9, "green": 0.3, "blue": 0.3},    # Vermelho
            "IMPRODUTIVO_PARCIAL": {"red": 1.0, "green": 0.6, "blue": 0.0},  # Laranja
            "PRODUTIVO_RESSALVA": {"red": 1.0, "green": 0.9, "blue": 0.2},   # Amarelo
            "PRODUTIVO": {"red": 0.4, "green": 0.8, "blue": 0.4},            # Verde
            "PENDENTE": {"red": 0.8, "green": 0.8, "blue": 0.8}              # Cinza
        }

        # Adiciona na ordem definida, depois os não previstos
        linhas_formatadas = []
        linha_atual = 3 # Começa na linha 3 da planilha
        
        for c in ordem_exibicao:
            if c in contagem or c in cores: # Mesmo se for 0, mostra para ficar bonito
                total = contagem.get(c, 0)
                dados_inserir.append([c, total])
                linhas_formatadas.append((linha_atual, cores.get(c, cores["PENDENTE"])))
                linha_atual += 1

        for c, count in contagem.items():
            if c not in ordem_exibicao and str(c).strip() != "":
                dados_inserir.append([c, count])
                linhas_formatadas.append((linha_atual, cores["PENDENTE"]))
                linha_atual += 1

        aba_dash.update('A1', dados_inserir)

        # 4. Formatação
        # Título
        aba_dash.format("A1:B1", {
            "backgroundColor": {"red": 0.1, "green": 0.2, "blue": 0.4},
            "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}, "bold": True, "fontSize": 12},
            "horizontalAlignment": "CENTER"
        })
        aba_dash.merge_cells("A1:B1")

        # Cabeçalho Tabela
        aba_dash.format("A2:B2", {
            "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
            "textFormat": {"bold": True},
            "horizontalAlignment": "CENTER"
        })

        # Cores para cada linha
        for linha_num, cor in linhas_formatadas:
            rng = f"A{linha_num}:B{linha_num}"
            aba_dash.format(rng, {
                "backgroundColor": cor,
                "textFormat": {"bold": True},
                "horizontalAlignment": "CENTER"
            })

        logger.info("Dashboard gerado com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro ao gerar dashboard: {e}")

if __name__ == "__main__":
    gerar_dashboard()
