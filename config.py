"""
config.py — Configurações e constantes do Agente Meteorológico
Tecomat Engenharia — Recife-PE
"""

import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env (se existir)
load_dotenv()

# ─── Google Sheets ────────────────────────────────────────────────────────────
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "service_account.json")

# Nomes das abas na planilha
ABA_OBRAS = "OBRAS"
ABA_REGISTROS = "REGISTROS_METEOROLOGICOS"

# ─── INMET ────────────────────────────────────────────────────────────────────
# URL base da API pública do INMET
INMET_API_BASE = "https://apitempo.inmet.gov.br"

# Estação automática oficial de Recife-PE
ESTACAO_PADRAO = "A301"

# ─── Fuso horário ─────────────────────────────────────────────────────────────
# A API do INMET retorna dados em UTC — convertemos para BRT (UTC-3)
TIMEZONE_BRT = "America/Recife"

# ─── Campos coletados da API INMET ───────────────────────────────────────────
# Mapeamento: campo da API → (descrição, método de agregação diária)
CAMPOS_INMET = {
    "CHUVA":   ("Precipitação (mm)", "sum"),
    "VEN_VEL": ("Vento Máx (m/s)",   "max"),
    "VEN_RAJ": ("Rajada (m/s)",       "max"),
    "UMD_MAX": ("Umidade Máx (%)",    "max"),
    "TEM_MAX": ("Temp. Máx (°C)",     "max"),
    "TEM_MIN": ("Temp. Mín (°C)",     "min"),
}

# ─── Cabeçalho da aba de registros ───────────────────────────────────────────
CABECALHO_REGISTROS = [
    "Data",
    "ID Obra",
    "Nome da Obra",
    "Precip. (mm)",
    "Vento Máx (m/s)",
    "Rajada (m/s)",
    "Umidade Máx (%)",
    "Temp. Máx (°C)",
    "Temp. Mín (°C)",
    "Fonte",
    "Classificação",
    "Observações",
]
