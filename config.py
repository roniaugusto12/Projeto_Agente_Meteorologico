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

# ─── Períodos de trabalho (hora BRT, inclusive) ──────────────────────────────
HORA_INICIO_MANHA     = 7    # 07h BRT
HORA_FIM_MANHA        = 11   # 11h BRT → H07, H08, H09, H10, H11 = 5 horas

HORA_INICIO_ALMOCO    = 12   # 12h BRT — EXCLUÍDO da análise
HORA_FIM_ALMOCO       = 12   # 12h BRT — EXCLUÍDO da análise (antes era até 13h)

HORA_INICIO_TARDE     = 13   # 13h BRT (após almoço)
HORA_FIM_TARDE_NORMAL = 16   # 16h BRT → H13, H14, H15, H16 = 4 horas (seg–qui)
HORA_FIM_TARDE_SEXTA  = 15   # 15h BRT → H13, H14, H15 = 3 horas (sex)

# ─── Thresholds horários ─────────────────────────────────────────────────────
CHUVA_HORA_ADVERSA   = 1.0   # mm/h — "chuva fraca" (WMO) → inviabiliza argamassa e pintura
CHUVA_HORA_ATENCAO   = 0.2   # mm/h — chuvisco → superfície úmida, atenção
RAJADA_IMPRODUTIVO   = 11.1  # m/s (40 km/h) — NR-35 Anexo I
RAJADA_ATENCAO       = 6.9   # m/s (25 km/h) — zona de atenção em andaimes

# ─── Thresholds de precipitação por período ──────────────────────────────────
# Manhã (4h)
CHUVA_MANHA_IMPRODUTIVO  = 8.0   # mm no período
CHUVA_MANHA_PARCIAL      = 2.0   # mm no período
CHUVA_MANHA_RESSALVA     = 0.5   # mm no período

# Tarde normal (3h, seg–qui)
CHUVA_TARDE_IMPRODUTIVO  = 6.0   # mm no período
CHUVA_TARDE_PARCIAL      = 1.5   # mm no período
CHUVA_TARDE_RESSALVA     = 0.5   # mm no período

# Tarde sexta (2h)
CHUVA_SEXTA_IMPRODUTIVO  = 4.0   # mm no período
CHUVA_SEXTA_PARCIAL      = 1.0   # mm no período
CHUVA_SEXTA_RESSALVA     = 0.5   # mm no período

# ─── Mínimo de horas adversas para IMPRODUTIVO (≈ 70% do turno) ──────────────
HORAS_IMP_MANHA          = 4     # de 5 horas → 80%
HORAS_IMP_TARDE_NORMAL   = 3     # de 4 horas → 75%
HORAS_IMP_TARDE_SEXTA    = 2     # de 3 horas → 66%

# ─── Critério combinado (chuva dirigida) ─────────────────────────────────────
CHUVA_DIRIGIDA_MM        = 5.0   # mm no período
CHUVA_DIRIGIDA_VENTO     = 6.9   # m/s

