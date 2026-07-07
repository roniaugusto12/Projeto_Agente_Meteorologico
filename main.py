"""
main.py — Ponto de entrada do Agente Meteorológico
Tecomat Engenharia — Recife-PE

Fluxo de execução:
  1. Lê as obras ativas da planilha Google Sheets (aba OBRAS)
  2. Para cada obra, coleta os dados meteorológicos do dia anterior via INMET
     (usando a estação vinculada à obra, ou a estação padrão A301)
  3. Grava os dados na aba REGISTROS_METEOROLOGICOS
  4. Evita duplicatas automaticamente

Agendamento: GitHub Actions — todos os dias às 06:00 BRT (09:00 UTC)
"""

import logging
import sys

# Corrige problema de exibição de emojis (UnicodeEncodeError) no terminal do Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from datetime import datetime
from zoneinfo import ZoneInfo

from config import ESTACAO_PADRAO, TIMEZONE_BRT
import argparse
from datetime import timedelta
from coletor.inmet_client import buscar_dados_horarios, agregar_dados_diarios
from coletor.alternativo_client import coletar_apac_dia_anterior, coletar_noticias_dia_anterior
from coletor.classificador import avaliar_consenso
from sheets.google_sheets_client import ler_obras, gravar_registro

# ─── Configuração de logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

BRT = ZoneInfo(TIMEZONE_BRT)


def executar():
    """Executa o ciclo completo de coleta e registro meteorológico."""
    parser = argparse.ArgumentParser(description="Agente Meteorológico — Tecomat Engenharia")
    parser.add_argument("--start-date", help="Data de início no formato AAAA-MM-DD")
    parser.add_argument("--end-date", help="Data de fim no formato AAAA-MM-DD")
    parser.add_argument("--non-interactive", action="store_true", help="Ignora prompts e usa o padrão (ontem)")
    args = parser.parse_args()

    hoje_brt = datetime.now(tz=BRT).date()
    ontem_brt = hoje_brt - timedelta(days=1)
    
    datas_alvo = []
    
    if args.start_date:
        try:
            start = datetime.strptime(args.start_date, "%Y-%m-%d").date()
            end = datetime.strptime(args.end_date, "%Y-%m-%d").date() if args.end_date else start
            if start > end:
                logger.error("A data de início não pode ser posterior à data de fim.")
                sys.exit(1)
            curr = start
            while curr <= end:
                datas_alvo.append(curr.strftime("%Y-%m-%d"))
                curr += timedelta(days=1)
        except ValueError as e:
            logger.error(f"Formato de data inválido. Use AAAA-MM-DD. Erro: {e}")
            sys.exit(1)
    elif not args.non_interactive:
        print("\n" + "=" * 60)
        print("🌤  Agente Meteorológico — Período de Análise")
        print("=" * 60)
        print("1. Ontem (padrão)")
        print("2. Últimos 7 dias (Semana anterior)")
        print("3. Período personalizado (especificar datas)")
        print("=" * 60)
        try:
            opcao = input("Opção [1-3] (padrão: 1): ").strip()
        except (KeyboardInterrupt, EOFError):
            opcao = "1"
        
        if opcao == "2":
            start = hoje_brt - timedelta(days=7)
            curr = start
            while curr <= ontem_brt:
                datas_alvo.append(curr.strftime("%Y-%m-%d"))
                curr += timedelta(days=1)
        elif opcao == "3":
            try:
                start_str = input("Data de início (AAAA-MM-DD): ").strip()
                end_str = input("Data de fim (AAAA-MM-DD): ").strip()
                start = datetime.strptime(start_str, "%Y-%m-%d").date()
                end = datetime.strptime(end_str, "%Y-%m-%d").date()
                if start > end:
                    print("Erro: A data de início não pode ser posterior à data de fim.")
                    sys.exit(1)
                curr = start
                while curr <= end:
                    datas_alvo.append(curr.strftime("%Y-%m-%d"))
                    curr += timedelta(days=1)
            except ValueError as e:
                print(f"Erro: Formato de data inválido. Use AAAA-MM-DD. Erro: {e}")
                sys.exit(1)
            except (KeyboardInterrupt, EOFError):
                sys.exit(0)
        else:
            datas_alvo.append(ontem_brt.strftime("%Y-%m-%d"))
    else:
        if hoje_brt.weekday() == 5:  # 5 represents Saturday in Python's weekday (0=Monday)
            logger.info("Execução automática de sábado detectada. Analisando a semana anterior (últimos 7 dias).")
            start = hoje_brt - timedelta(days=7)
            curr = start
            while curr <= ontem_brt:
                datas_alvo.append(curr.strftime("%Y-%m-%d"))
                curr += timedelta(days=1)
        else:
            datas_alvo.append(ontem_brt.strftime("%Y-%m-%d"))

    agora = datetime.now(tz=BRT)
    logger.info("=" * 60)
    logger.info(f"🌤  Agente Meteorológico — Tecomat Engenharia")
    logger.info(f"📅  Execução em: {agora.strftime('%d/%m/%Y %H:%M:%S')} BRT")
    logger.info(f"📅  Período selecionado: {datas_alvo[0]} até {datas_alvo[-1]} ({len(datas_alvo)} dia(s))")
    logger.info("=" * 60)

    # ── 1. Lê obras ativas ───────────────────────────────────────────────────
    try:
        obras = ler_obras()
    except Exception as e:
        logger.error(f"Falha ao ler obras da planilha: {e}")
        sys.exit(1)

    if not obras:
        logger.warning("Nenhuma obra ativa encontrada na planilha. Encerrando.")
        return

    logger.info(f"📋 {len(obras)} obra(s) ativa(s) encontrada(s).")

    # ── 2. Coleta e Gravação em Loop para cada data ──────────────────────────
    linhas_a_gravar = []
    
    try:
        from sheets.google_sheets_client import _abrir_planilha, ABA_REGISTROS, _garantir_cabecalho
        planilha = _abrir_planilha()
        aba = planilha.worksheet(ABA_REGISTROS)
        _garantir_cabecalho(aba)
        todos_existentes = aba.get_all_values()
        
        chaves_existentes = set()
        if len(todos_existentes) > 1:
            for linha in todos_existentes[1:]:
                if len(linha) >= 2:
                    chaves_existentes.add((linha[0], str(linha[1])))
    except Exception as e:
        logger.error(f"Falha ao conectar e ler registros existentes da planilha: {e}")
        sys.exit(1)

    gravados    = 0
    duplicatas  = 0
    erros       = 0

    for data_str in datas_alvo:
        logger.info(f"\n📅 === Processando dia: {data_str} ===")
        estacoes_coletadas: dict[str, dict | None] = {}

        for obra in obras:
            nome_obra = obra.get("Nome da Obra", f"ID {obra.get('ID')}")
            estacao   = str(obra.get("Estação INMET", ESTACAO_PADRAO)).strip() or ESTACAO_PADRAO
            id_obra   = str(obra.get("ID", ""))

            logger.info(f"─── {nome_obra} (estação {estacao}) ───")

            if estacao not in estacoes_coletadas:
                registros_inmet = buscar_dados_horarios(data_str, estacao)
                agregado_inmet, regs_inmet = agregar_dados_diarios(registros_inmet, data_str) if registros_inmet else (None, [])
                
                regs_apac = coletar_apac_dia_anterior(estacao, data_str)
                noticia = coletar_noticias_dia_anterior(data_str)
                
                classificacao, observacoes = avaliar_consenso(regs_inmet, regs_apac, noticia, data_str)
                
                if agregado_inmet:
                    dados = agregado_inmet.copy()
                    dados["classificacao"] = classificacao
                    dados["observacoes"] = observacoes
                    dados["fonte"] = "INMET + APAC + Notícias"
                else:
                    agregado_apac = None
                    if regs_apac:
                        agregado_apac_tuple = agregar_dados_diarios(regs_apac, data_str)
                        if agregado_apac_tuple:
                            agregado_apac = agregado_apac_tuple[0]
                    
                    if agregado_apac:
                        dados = agregado_apac.copy()
                        dados["classificacao"] = classificacao
                        dados["observacoes"] = observacoes
                        dados["fonte"] = "APAC (Simulada) + Notícias"
                    else:
                        dados = {
                            "data": data_str,
                            "precipitacao": 0.0,
                            "vento_max": 0.0,
                            "rajada_max": 0.0,
                            "umidade_max": 0.0,
                            "temp_max": 0.0,
                            "temp_min": 0.0,
                            "fonte": "Sem Dados (Apenas Notícias)",
                            "total_horas": 0,
                            "classificacao": classificacao,
                            "observacoes": observacoes,
                        }
                
                estacoes_coletadas[estacao] = dados
            else:
                dados = estacoes_coletadas[estacao]
                if dados:
                    logger.info(f"Reutilizando dados já coletados para estação {estacao} no dia {data_str}.")

            if not dados:
                logger.error(f"Sem dados meteorológicos para {nome_obra} — estação {estacao} no dia {data_str}.")
                erros += 1
                continue

            # Filtra e ignora registros classificados como PRODUTIVO
            if dados.get("classificacao") == "PRODUTIVO":
                logger.info(f"Skip: Dia {data_str} classificado como PRODUTIVO. Não gravado conforme preferências.")
                continue

            chave = (data_str, id_obra)
            if chave in chaves_existentes:
                logger.info(f"Registro já existe para {data_str} / Obra {id_obra} — ignorando.")
                duplicatas += 1
                continue

            def fmt(valor):
                return str(valor).replace(".", ",") if valor is not None else ""

            nova_linha = [
                data_str,
                id_obra,
                obra.get("Nome da Obra", ""),
                fmt(dados.get("precipitacao")),
                fmt(dados.get("vento_max")),
                fmt(dados.get("rajada_max")),
                fmt(dados.get("umidade_max")),
                fmt(dados.get("temp_max")),
                fmt(dados.get("temp_min")),
                dados.get("fonte", "INMET"),
                dados.get("classificacao", "PENDENTE"),
                dados.get("observacoes", ""),
            ]
            linhas_a_gravar.append((nova_linha, nome_obra, data_str))
            chaves_existentes.add(chave)

    # ── 3. Gravação em Lote no Sheets ────────────────────────────────────────
    if linhas_a_gravar:
        logger.info(f"\n✍️  Gravando {len(linhas_a_gravar)} registros no Google Sheets em lote...")
        try:
            valores_lote = [item[0] for item in linhas_a_gravar]
            aba.append_rows(valores_lote, value_input_option="USER_ENTERED")
            for item in linhas_a_gravar:
                logger.info(f"✅ Registro gravado: {item[2]} | Obra: {item[1]}")
            gravados = len(linhas_a_gravar)
        except Exception as e:
            logger.error(f"Erro ao gravar os registros em lote no Google Sheets: {e}")
            erros += len(linhas_a_gravar)
    else:
        logger.info("\n⏭️  Nenhum novo registro a gravar no Google Sheets.")

    # ── 4. Resumo final ───────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info(f"✅  Registros Gravados: {gravados}")
    logger.info(f"⏭️   Duplicatas:        {duplicatas}")
    logger.info(f"❌  Erros/Falhas:      {erros}")
    logger.info("=" * 60)

    if erros > 0:
        sys.exit(1)


if __name__ == "__main__":
    executar()
