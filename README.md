# Agente Meteorológico — Tecomat Engenharia

Sistema automatizado de coleta e registro de dados meteorológicos para subsidiar a fiscalização de obras de fachada em Recife-PE.

---

## O que o sistema faz

- Coleta diariamente os dados meteorológicos da estação **INMET A301 (Recife)** via API pública
- Registra precipitação, vento, rajada, umidade e temperatura do dia anterior
- Armazena os dados automaticamente em uma planilha **Google Sheets**
- Executa sozinho todos os dias às **06:00 BRT** via **GitHub Actions** — sem intervenção humana

---

## Pré-requisitos

- Python 3.12+
- Conta Google Cloud (para a Service Account)
- Planilha Google Sheets criada
- Conta GitHub com este repositório

---

## Configuração passo a passo

### 1. Criar a planilha Google Sheets

1. Acesse [Google Sheets](https://sheets.google.com) e crie uma planilha nova
2. Renomeie a primeira aba para `OBRAS`
3. Crie uma segunda aba chamada `REGISTROS_METEOROLOGICOS`
4. Na aba `OBRAS`, crie o seguinte cabeçalho na linha 1:

| ID | Nome da Obra | Endereço | Bairro | CEP | Latitude | Longitude | Estação INMET | Status |
|---|---|---|---|---|---|---|---|---|

> A coluna **Estação INMET** deve ser preenchida com `A301` para todas as obras em Recife.  
> A coluna **Status** deve conter `ATIVO` para que a obra seja coletada.

5. Copie o **ID da planilha** da URL:  
   `https://docs.google.com/spreadsheets/d/`**`SEU_ID_AQUI`**`/edit`

---

### 2. Criar a Service Account no Google Cloud

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um projeto (ou use um existente)
3. Ative as APIs:
   - **Google Sheets API**
   - **Google Drive API**
4. Vá em **IAM e Admin → Contas de Serviço → Criar conta de serviço**
5. Dê um nome (ex: `agente-meteorologico`) e clique em **Criar**
6. Em **Chaves**, clique em **Adicionar chave → JSON** — um arquivo será baixado
7. **Compartilhe a planilha** com o e-mail da Service Account (ex: `agente-meteorologico@projeto.iam.gserviceaccount.com`) com permissão de **Editor**

---

### 3. Configurar o ambiente local (desenvolvimento)

```bash
# Clone o repositório
git clone https://github.com/roniaugusto12/Projeto-Agente-Meteorol-gico-.git
cd "Projeto-Agente-Meteorol-gico-"

# Crie o ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
copy .env.example .env
```

Edite o arquivo `.env` com seus valores:

```env
GOOGLE_SHEETS_ID=seu_id_da_planilha
GOOGLE_SERVICE_ACCOUNT_JSON=service_account.json
```

Coloque o arquivo `service_account.json` (baixado do Google Cloud) na raiz do projeto.

---

### 4. Executar localmente

```bash
python main.py
```

---

### 5. Configurar o GitHub Actions (execução automática)

1. No GitHub, vá em **Settings → Secrets and variables → Actions → New repository secret**
2. Crie os seguintes secrets:

| Secret | Valor |
|---|---|
| `GOOGLE_SHEETS_ID` | ID da sua planilha Google Sheets |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | **Conteúdo completo** do arquivo `service_account.json` (cole o JSON inteiro) |

3. O agente passará a rodar automaticamente todos os dias às **06:00 BRT**
4. Para executar manualmente: **Actions → Coletor Meteorológico Diário → Run workflow**

---

## Estrutura do projeto

```
projeto 01/
├── .github/
│   └── workflows/
│       └── coletor_diario.yml      # Agendamento automático
├── coletor/
│   ├── __init__.py
│   └── inmet_client.py             # Coleta INMET + agregação diária
├── sheets/
│   ├── __init__.py
│   └── google_sheets_client.py     # Leitura de obras + gravação
├── config.py                       # Configurações e constantes
├── main.py                         # Ponto de entrada do agente
├── requirements.txt                # Dependências Python
├── .env.example                    # Template de variáveis de ambiente
└── README.md                       # Este arquivo
```

---

## Roadmap

| Fase | Descrição | Status |
|---|---|---|
| **MVP (Fase 1)** | Coleta INMET + Google Sheets + GitHub Actions | ✅ Implementado |
| Fase 2 | Critérios de classificação de dia improdutivo | ⏳ Aguardando |
| Fase 3 | Integração com APAC | ⏳ Aguardando |
| Fase 4 | Dashboard Google Looker Studio | ⏳ Planejada |
| Fase 5 | Relatório mensal automatizado | ⏳ Planejada |

---

*Tecomat Engenharia — Recife-PE*
