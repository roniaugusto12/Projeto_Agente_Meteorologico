"""
google_sheets_client.py — Integração com Google Sheets via gspread
Tecomat Engenharia — Recife-PE

Responsabilidades:
  - Ler a aba OBRAS para obter as obras ativas e suas estações INMET
  - Gravar os registros meteorológicos diários na aba REGISTROS_METEOROLOGICOS
  - Evitar duplicatas (verifica se já existe registro para data + obra)
  - Criar o cabeçalho automaticamente se a aba estiver vazia
"""

import json
import logging
import os

import gspread
from google.oauth2.service_account import Credentials

from config import (
    GOOGLE_SHEETS_ID,
    GOOGLE_SERVICE_ACCOUNT_JSON,
    ABA_OBRAS,
    ABA_REGISTROS,
    CABECALHO_REGISTROS,
    ESTACAO_PADRAO,
)

logger = logging.getLogger(__name__)

# Escopos necessários para leitura e escrita no Google Sheets
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _autenticar() -> gspread.Client:
    """
    Autentica com o Google usando Service Account.

    O JSON da service account pode ser fornecido de duas formas:
      1. Variável de ambiente GOOGLE_SERVICE_ACCOUNT_JSON contendo o JSON completo (GitHub Actions)
      2. Caminho para um arquivo .json local (desenvolvimento)
    """
    json_env = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")

    # Tenta carregar como JSON inline (GitHub Actions usa secret como conteúdo do arquivo)
    try:
        info = json.loads(json_env)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        logger.info("Autenticado via variável de ambiente (JSON inline).")
        return gspread.authorize(creds)
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: carrega de arquivo local
    caminho = json_env if json_env else GOOGLE_SERVICE_ACCOUNT_JSON
    if not os.path.exists(caminho):
        raise FileNotFoundError(
            f"Arquivo de credenciais não encontrado: '{caminho}'. "
            "Configure a variável GOOGLE_SERVICE_ACCOUNT_JSON no .env."
        )
    creds = Credentials.from_service_account_file(caminho, scopes=SCOPES)
    logger.info(f"Autenticado via arquivo: {caminho}")
    return gspread.authorize(creds)


def _abrir_planilha() -> gspread.Spreadsheet:
    """Abre a planilha do Google Sheets configurada."""
    if not GOOGLE_SHEETS_ID:
        raise ValueError(
            "GOOGLE_SHEETS_ID não configurado. Verifique o arquivo .env."
        )
    cliente = _autenticar()
    return cliente.open_by_key(GOOGLE_SHEETS_ID)


def ler_obras() -> list[dict]:
    """
    Lê a aba OBRAS e retorna as obras ativas.

    Colunas esperadas (nomes no cabeçalho):
        ID | Nome da Obra | Endereço | Bairro | CEP | Latitude | Longitude | Estação INMET | Status

    Returns:
        Lista de dicts com os dados de cada obra ativa (Status == "ATIVO").
    """
    planilha = _abrir_planilha()
    aba = planilha.worksheet(ABA_OBRAS)
    registros = aba.get_all_records()

    obras_ativas = [
        obra for obra in registros
        if str(obra.get("Status", "")).strip().upper() == "ATIVO"
    ]

    logger.info(f"Obras ativas encontradas: {len(obras_ativas)}")
    return obras_ativas


def _garantir_cabecalho(aba: gspread.Worksheet) -> None:
    """Cria o cabeçalho na aba de registros se ela estiver vazia."""
    if aba.row_count == 0 or not aba.row_values(1):
        aba.append_row(CABECALHO_REGISTROS, value_input_option="RAW")
        logger.info("Cabeçalho criado na aba de registros.")


def _ja_existe_registro(aba: gspread.Worksheet, data: str, id_obra: str) -> bool:
    """
    Verifica se já existe um registro para a combinação data + ID da obra.
    Evita duplicatas em caso de reexecução do agente no mesmo dia.
    """
    todos = aba.get_all_values()
    if len(todos) <= 1:
        return False

    for linha in todos[1:]:  # pula cabeçalho
        if len(linha) >= 2 and linha[0] == data and linha[1] == str(id_obra):
            return True
    return False


def gravar_registro(dados_meteo: dict, obra: dict) -> bool:
    """
    Grava um registro meteorológico diário na aba REGISTROS_METEOROLOGICOS.

    Args:
        dados_meteo: Dicionário retornado por inmet_client.agregar_dados_diarios()
        obra: Dicionário com os dados da obra (lido da aba OBRAS)

    Returns:
        True se o registro foi gravado, False se já existia (duplicata) ou erro.
    """
    if not dados_meteo:
        logger.warning("Dados meteorológicos vazios — nada a gravar.")
        return False

    planilha = _abrir_planilha()
    aba = planilha.worksheet(ABA_REGISTROS)
    _garantir_cabecalho(aba)

    data    = dados_meteo.get("data", "")
    id_obra = str(obra.get("ID", ""))

    if _ja_existe_registro(aba, data, id_obra):
        logger.info(f"Registro já existe para {data} / Obra {id_obra} — ignorando.")
        return False

    def fmt(valor):
        """Formata número ou retorna string vazia para None."""
        return str(valor).replace(".", ",") if valor is not None else ""

    nova_linha = [
        data,
        id_obra,
        obra.get("Nome da Obra", ""),
        fmt(dados_meteo.get("precipitacao")),
        fmt(dados_meteo.get("vento_max")),
        fmt(dados_meteo.get("rajada_max")),
        fmt(dados_meteo.get("umidade_max")),
        fmt(dados_meteo.get("temp_max")),
        fmt(dados_meteo.get("temp_min")),
        dados_meteo.get("fonte", "INMET"),
        dados_meteo.get("classificacao", "PRODUTIVO"),
        dados_meteo.get("observacoes", ""),
    ]

    aba.append_row(nova_linha, value_input_option="USER_ENTERED")
    logger.info(f"✅ Registro gravado: {data} | Obra: {obra.get('Nome da Obra')} | Chuva: {dados_meteo.get('precipitacao')}mm")
    return True
