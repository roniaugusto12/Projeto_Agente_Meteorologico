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
from datetime import datetime
from zoneinfo import ZoneInfo

from config import ESTACAO_PADRAO, TIMEZONE_BRT
from coletor.alternativo_client import coletar_dia_anterior_alternativo as coletar_dia_anterior
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

    agora = datetime.now(tz=BRT)
    logger.info("=" * 60)
    logger.info(f"🌤  Agente Meteorológico — Tecomat Engenharia")
    logger.info(f"📅  Execução em: {agora.strftime('%d/%m/%Y %H:%M:%S')} BRT")
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

    # ── 2. Coleta dados para cada obra ────────────────────────────────────────
    gravados    = 0
    duplicatas  = 0
    erros       = 0

    # Agrupa obras por estação para evitar chamadas duplicadas à API
    estacoes_coletadas: dict[str, dict | None] = {}

    for obra in obras:
        nome_obra = obra.get("Nome da Obra", f"ID {obra.get('ID')}")
        estacao   = str(obra.get("Estação INMET", ESTACAO_PADRAO)).strip() or ESTACAO_PADRAO

        logger.info(f"─── Processando: {nome_obra} (estação {estacao}) ───")

        # Reaproveita coleta se a mesma estação já foi consultada
        if estacao not in estacoes_coletadas:
            dados = coletar_dia_anterior(estacao)
            estacoes_coletadas[estacao] = dados
        else:
            dados = estacoes_coletadas[estacao]
            if dados:
                logger.info(f"Reutilizando dados já coletados para estação {estacao}.")

        if not dados:
            logger.error(f"Sem dados meteorológicos para {nome_obra} — estação {estacao}.")
            erros += 1
            continue

        # ── 3. Grava na planilha ─────────────────────────────────────────────
        try:
            gravado = gravar_registro(dados, obra)
            if gravado:
                gravados += 1
            else:
                duplicatas += 1
        except Exception as e:
            logger.error(f"Erro ao gravar registro de {nome_obra}: {e}")
            erros += 1

    # ── 4. Resumo final ───────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info(f"✅  Gravados:    {gravados}")
    logger.info(f"⏭️   Duplicatas:  {duplicatas}")
    logger.info(f"❌  Erros:       {erros}")
    logger.info("=" * 60)

    if erros > 0:
        sys.exit(1)


if __name__ == "__main__":
    executar()
