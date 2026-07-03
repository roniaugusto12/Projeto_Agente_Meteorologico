"""
setup_automatico.py — Script de configuração automática do Agente Meteorológico
Tecomat Engenharia — Recife-PE

Este script realiza toda a configuração necessária:
  1. Cria um projeto no Google Cloud (ou usa um existente)
  2. Habilita as APIs necessárias (Sheets + Drive)
  3. Cria a Service Account e baixa as credenciais JSON
  4. Cria a planilha Google Sheets com as abas corretas e cabeçalhos
  5. Compartilha a planilha com a Service Account
  6. Cria o arquivo .env com as configurações
  7. Configura os Secrets no repositório do GitHub

Pré-requisitos (feitos automaticamente pelo setup.ps1):
  - gcloud autenticado (gcloud auth login)
  - gh autenticado (gh auth login)
"""

import subprocess
import json
import sys
import os
import time

# ─── Configurações do projeto ─────────────────────────────────────────────────
GCP_PROJECT_ID   = "tecomat-agente-meteo"       # ID único no Google Cloud
GCP_PROJECT_NAME = "Tecomat Agente Meteorologico"
SA_NAME          = "agente-meteorologico"        # Nome da service account
SA_DISPLAY_NAME  = "Agente Meteorologico Tecomat"
KEY_FILE         = "service_account.json"        # Arquivo de credenciais local
SHEET_NAME       = "Agente Meteorologico - Tecomat"
GITHUB_REPO      = "roniaugusto12/Projeto-Agente-Meteorol-gico-"
# ─────────────────────────────────────────────────────────────────────────────


def run(cmd: list[str], check=True, capture=True) -> subprocess.CompletedProcess:
    """Executa um comando e retorna o resultado."""
    result = subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    if check and result.returncode != 0:
        print(f"\n❌ ERRO ao executar: {' '.join(cmd)}")
        print(f"   {result.stderr.strip()}")
        sys.exit(1)
    return result


def step(msg: str):
    print(f"\n{'─'*60}")
    print(f"  {msg}")
    print(f"{'─'*60}")


# ══════════════════════════════════════════════════════════════
# PASSO 1 — Criar projeto Google Cloud
# ══════════════════════════════════════════════════════════════
step("1/7 — Verificando projeto Google Cloud...")

# Verifica se o projeto já existe
check = run(["gcloud", "projects", "describe", GCP_PROJECT_ID], check=False)
if check.returncode == 0:
    print(f"✅ Projeto '{GCP_PROJECT_ID}' já existe — usando o existente.")
else:
    print(f"📦 Criando projeto '{GCP_PROJECT_ID}'...")
    run(["gcloud", "projects", "create", GCP_PROJECT_ID,
         "--name", GCP_PROJECT_NAME])
    print(f"✅ Projeto criado!")

# Define como projeto padrão
run(["gcloud", "config", "set", "project", GCP_PROJECT_ID])
print(f"✅ Projeto '{GCP_PROJECT_ID}' definido como padrão.")


# ══════════════════════════════════════════════════════════════
# PASSO 2 — Habilitar as APIs necessárias
# ══════════════════════════════════════════════════════════════
step("2/7 — Habilitando APIs do Google...")

apis = ["sheets.googleapis.com", "drive.googleapis.com"]
for api in apis:
    print(f"   Habilitando {api}...")
    run(["gcloud", "services", "enable", api, "--project", GCP_PROJECT_ID])
    print(f"   ✅ {api} habilitada.")

print("\n✅ APIs habilitadas com sucesso!")


# ══════════════════════════════════════════════════════════════
# PASSO 3 — Criar Service Account e baixar credenciais
# ══════════════════════════════════════════════════════════════
step("3/7 — Criando Service Account...")

SA_EMAIL = f"{SA_NAME}@{GCP_PROJECT_ID}.iam.gserviceaccount.com"

# Verifica se a service account já existe
check = run(["gcloud", "iam", "service-accounts", "describe", SA_EMAIL,
             "--project", GCP_PROJECT_ID], check=False)

if check.returncode == 0:
    print(f"✅ Service account '{SA_EMAIL}' já existe.")
else:
    run(["gcloud", "iam", "service-accounts", "create", SA_NAME,
         "--display-name", SA_DISPLAY_NAME,
         "--project", GCP_PROJECT_ID])
    print(f"✅ Service account criada: {SA_EMAIL}")

# Baixa a chave JSON
if os.path.exists(KEY_FILE):
    print(f"✅ Arquivo '{KEY_FILE}' já existe — pulando download.")
else:
    print(f"🔑 Baixando chave JSON...")
    run(["gcloud", "iam", "service-accounts", "keys", "create", KEY_FILE,
         "--iam-account", SA_EMAIL,
         "--project", GCP_PROJECT_ID])
    print(f"✅ Credenciais salvas em '{KEY_FILE}'")


# ══════════════════════════════════════════════════════════════
# PASSO 4 — Criar a planilha Google Sheets
# ══════════════════════════════════════════════════════════════
step("4/7 — Criando planilha Google Sheets...")

# Instala gspread se necessário
try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("📦 Instalando dependências Python...")
    subprocess.run([sys.executable, "-m", "pip", "install", "gspread", "google-auth", "--quiet"])
    import gspread
    from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds  = Credentials.from_service_account_file(KEY_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

# Verifica se a planilha já existe
sheets_existentes = client.list_spreadsheet_files()
planilha_existente = next(
    (s for s in sheets_existentes if s["name"] == SHEET_NAME), None
)

if planilha_existente:
    planilha   = client.open(SHEET_NAME)
    SHEETS_ID  = planilha.id
    print(f"✅ Planilha já existe: {SHEET_NAME}")
else:
    planilha  = client.create(SHEET_NAME)
    SHEETS_ID = planilha.id
    print(f"✅ Planilha criada: {SHEET_NAME}")

print(f"   ID: {SHEETS_ID}")

# ── Aba OBRAS ────────────────────────────────────────────────
try:
    aba_obras = planilha.worksheet("OBRAS")
    print("   ✅ Aba 'OBRAS' já existe.")
except gspread.WorksheetNotFound:
    # Renomeia a Sheet1 padrão
    try:
        sheet1 = planilha.worksheet("Sheet1")
        sheet1.update_title("OBRAS")
        aba_obras = sheet1
    except gspread.WorksheetNotFound:
        aba_obras = planilha.add_worksheet(title="OBRAS", rows=1000, cols=10)
    print("   ✅ Aba 'OBRAS' criada.")

# Cabeçalho OBRAS
cabecalho_obras = [
    "ID", "Nome da Obra", "Endereço", "Bairro", "CEP",
    "Latitude", "Longitude", "Estação INMET", "Status"
]
if not aba_obras.row_values(1):
    aba_obras.append_row(cabecalho_obras)
    print("   ✅ Cabeçalho da aba OBRAS criado.")

# ── Aba REGISTROS_METEOROLOGICOS ──────────────────────────────
try:
    aba_reg = planilha.worksheet("REGISTROS_METEOROLOGICOS")
    print("   ✅ Aba 'REGISTROS_METEOROLOGICOS' já existe.")
except gspread.WorksheetNotFound:
    aba_reg = planilha.add_worksheet(
        title="REGISTROS_METEOROLOGICOS", rows=10000, cols=12
    )
    print("   ✅ Aba 'REGISTROS_METEOROLOGICOS' criada.")

cabecalho_reg = [
    "Data", "ID Obra", "Nome da Obra", "Precip. (mm)",
    "Vento Máx (m/s)", "Rajada (m/s)", "Umidade Máx (%)",
    "Temp. Máx (°C)", "Temp. Mín (°C)", "Fonte", "Classificação", "Observações"
]
if not aba_reg.row_values(1):
    aba_reg.append_row(cabecalho_reg)
    print("   ✅ Cabeçalho da aba REGISTROS criado.")

# ── Compartilha com a service account ────────────────────────
planilha.share(SA_EMAIL, perm_type="user", role="writer", notify=False)
print(f"   ✅ Planilha compartilhada com {SA_EMAIL}")

# ── Torna acessível para o usuário também ────────────────────
planilha.share(None, perm_type="anyone", role="reader")
print(f"   🔗 Link da planilha: https://docs.google.com/spreadsheets/d/{SHEETS_ID}/edit")


# ══════════════════════════════════════════════════════════════
# PASSO 5 — Criar arquivo .env
# ══════════════════════════════════════════════════════════════
step("5/7 — Criando arquivo .env...")

env_content = f"""# Gerado automaticamente pelo setup_automatico.py
GOOGLE_SHEETS_ID={SHEETS_ID}
GOOGLE_SERVICE_ACCOUNT_JSON={KEY_FILE}
"""

with open(".env", "w", encoding="utf-8") as f:
    f.write(env_content)

print(f"✅ Arquivo .env criado com GOOGLE_SHEETS_ID={SHEETS_ID}")


# ══════════════════════════════════════════════════════════════
# PASSO 6 — Configurar Secrets no GitHub
# ══════════════════════════════════════════════════════════════
step("6/7 — Configurando Secrets no GitHub...")

# Lê o conteúdo do service_account.json para usar como secret
with open(KEY_FILE, "r", encoding="utf-8") as f:
    sa_json_content = f.read()

# Configura GOOGLE_SHEETS_ID
result1 = run(
    ["gh", "secret", "set", "GOOGLE_SHEETS_ID",
     "--body", SHEETS_ID,
     "--repo", GITHUB_REPO],
    check=False
)
if result1.returncode == 0:
    print("   ✅ Secret GOOGLE_SHEETS_ID configurado no GitHub.")
else:
    print(f"   ⚠️  Falha ao configurar GOOGLE_SHEETS_ID: {result1.stderr.strip()}")

# Configura GOOGLE_SERVICE_ACCOUNT_JSON (conteúdo completo do JSON)
result2 = run(
    ["gh", "secret", "set", "GOOGLE_SERVICE_ACCOUNT_JSON",
     "--body", sa_json_content,
     "--repo", GITHUB_REPO],
    check=False
)
if result2.returncode == 0:
    print("   ✅ Secret GOOGLE_SERVICE_ACCOUNT_JSON configurado no GitHub.")
else:
    print(f"   ⚠️  Falha ao configurar GOOGLE_SERVICE_ACCOUNT_JSON: {result2.stderr.strip()}")


# ══════════════════════════════════════════════════════════════
# PASSO 7 — Testar a API do INMET
# ══════════════════════════════════════════════════════════════
step("7/7 — Testando a API do INMET...")

try:
    import requests
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    BRT = ZoneInfo("America/Recife")
    ontem = (datetime.now(tz=BRT) - timedelta(days=1)).strftime("%Y-%m-%d")
    url   = f"https://apitempo.inmet.gov.br/estacao/{ontem}/{ontem}/A301"

    print(f"   Consultando: {url}")
    resp  = requests.get(url, timeout=15)
    dados = resp.json()

    if dados:
        chuva_total = sum(
            float(h.get("CHUVA") or 0)
            for h in dados
            if h.get("CHUVA") not in (None, "", "null")
        )
        print(f"   ✅ API INMET respondeu! {len(dados)} registros horários para {ontem}")
        print(f"   🌧  Precipitação total ontem: {chuva_total:.1f}mm")
    else:
        print(f"   ⚠️  API retornou dados vazios para {ontem} — pode ser dia sem medição.")
except Exception as e:
    print(f"   ⚠️  Erro ao testar INMET: {e}")


# ══════════════════════════════════════════════════════════════
# RESUMO FINAL
# ══════════════════════════════════════════════════════════════
print(f"\n{'═'*60}")
print("  ✅  CONFIGURAÇÃO COMPLETA!")
print(f"{'═'*60}")
print(f"""
  📊 Planilha Google Sheets:
     https://docs.google.com/spreadsheets/d/{SHEETS_ID}/edit

  🔑 Credenciais: {KEY_FILE}
  📄 Variáveis:   .env

  🚀 Para testar o agente agora:
     python main.py

  ⏰ Execução automática: todos os dias às 06:00 BRT
     (GitHub Actions — .github/workflows/coletor_diario.yml)
""")
print(f"{'═'*60}\n")
