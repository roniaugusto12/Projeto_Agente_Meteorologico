# Contexto do Projeto — Agente de Monitoramento Meteorológico
**Empresa:** Tecomat Engenharia — Recife-PE
**Área:** Fiscalização de obras de fachada em prédios residenciais
**Data de início:** 03/07/2026
**Arquivo criado por:** Antigravity (IA) com base nas decisões do chat

---

## 1. Problema que o projeto resolve

A empresa realiza **duas visitas semanais** às obras fiscalizadas. Nos dias de chuva em que não há produção, as empresas executoras não registram esses dias como perdidos — elas os adicionam ao final do cronograma.

Como não há controle via **diário de obra**, a Tecomat fica dependente das informações fornecidas pelas próprias empresas executoras, o que compromete a imparcialidade da fiscalização e o controle do cronograma.

**Solução proposta:** Um agente automatizado que coleta dados meteorológicos diariamente de fontes externas confiáveis e registra os dias de chuva que inviabilizam a produção, vinculando essas informações ao endereço de cada obra.

---

## 2. Objetivo do sistema

- Coletar dados meteorológicos diariamente de forma automatizada
- Identificar e registrar dias de chuva que inviabilizam o trabalho externo em fachadas
- Vincular os registros ao endereço de cada obra fiscalizada
- Armazenar os dados em planilha Google Sheets acessível online
- Subsidiar os relatórios mensais de fiscalização com dados objetivos e rastreáveis

---

## 3. Fontes de dados definidas

| Fonte | Status no MVP | Observação |
|---|---|---|
| **INMET** (Instituto Nacional de Meteorologia) | ✅ Ativo no MVP | API pública, sem necessidade de cadastro ou chave |
| **APAC** (Agência Pernambucana de Águas e Clima) | ⏳ Fase 2 | API existe mas documentação não é pública — contato necessário |
| **Telejornais / portais locais** | ⏳ Fase futura | G1 PE, JC, NE10 — via RSS ou LLM |

**Contato APAC para acesso à API:** monitoramento@apac.pe.gov.br

---

## 4. Estação meteorológica de referência

| Código | Tipo | Local |
|---|---|---|
| **A301** | Automática (INMET) | Recife, PE — **estação principal do MVP** |
| 82900 | Convencional (INMET/BDMEP) | Recife, PE — dados históricos, acesso manual |

> A estação A301 é a estação automática oficial do INMET para Recife-PE.
> Os dados são horários e serão **agregados para totais/máximos diários** pelo sistema.

---

## 5. Dados coletados por dia (campos)

| Campo INMET | Descrição | Agregação |
|---|---|---|
| `CHUVA` | Precipitação (mm) | Soma diária |
| `VEN_VEL` | Velocidade do vento (m/s) | Máximo diário |
| `VEN_RAJ` | Rajada de vento (m/s) | Máximo diário |
| `UMD_MAX` | Umidade relativa máxima (%) | Máximo diário |
| `TEM_MAX` | Temperatura máxima (°C) | Máximo diário |
| `TEM_MIN` | Temperatura mínima (°C) | Mínimo diário |

> Todos os horários da API INMET são **UTC**. O sistema converte automaticamente para **BRT (UTC-3)**.

---

## 6. Armazenamento — Google Sheets

**Estrutura da planilha (duas abas):**

### Aba `OBRAS` — cadastro manual
| ID | Nome da Obra | Endereço | Bairro | CEP | Latitude | Longitude | Estação INMET | Status |
|---|---|---|---|---|---|---|---|---|

### Aba `REGISTROS_METEOROLOGICOS` — preenchida automaticamente
| Data | ID Obra | Nome da Obra | Precip. (mm) | Vento Máx (m/s) | Rajada (m/s) | Umidade Máx (%) | Temp. Máx (°C) | Temp. Mín (°C) | Fonte | Classificação | Observações |
|---|---|---|---|---|---|---|---|---|---|---|---|

> A coluna **Classificação** ficará como `PENDENTE` até a Fase 2, quando os critérios de dia improdutivo serão definidos com base em normas técnicas.

---

## 7. Stack tecnológico definido

| Componente | Ferramenta | Justificativa |
|---|---|---|
| Linguagem | **Python 3.12** | Ecossistema ideal para APIs, automação e dados |
| Coleta INMET | **requests** (HTTP) | API REST sem autenticação |
| Coleta APAC | **BeautifulSoup** / scraping | Fase futura |
| Google Sheets | **gspread + google-auth** | Biblioteca consolidada |
| Autenticação Sheets | **Service Account** | Funciona sem login manual — ideal para automação |
| Agendador | **GitHub Actions** (gratuito) | Cron diário, sem servidor próprio |
| Horário de execução | **06:00 BRT** (09:00 UTC) | `cron: '0 9 * * *'` |

---

## 8. Estrutura de pastas do projeto

```
projeto 01/
├── .github/
│   └── workflows/
│       └── coletor_diario.yml      # Agendamento automático GitHub Actions
├── coletor/
│   ├── __init__.py
│   ├── inmet_client.py             # Coleta e agregação de dados INMET
│   └── apac_scraper.py             # APAC — fase futura
├── sheets/
│   ├── __init__.py
│   └── google_sheets_client.py     # Leitura de obras + gravação de registros
├── config.py                       # Configurações e constantes
├── main.py                         # Ponto de entrada do agente
├── requirements.txt                # Dependências Python
├── .env.example                    # Template de variáveis de ambiente
├── CONTEXTO_PROJETO.md             # Este arquivo
└── README.md                       # Guia de configuração passo a passo
```

---

## 9. Decisões explicitamente tomadas

| # | Decisão | Escolha | Motivo |
|---|---|---|---|
| 1 | Linguagem de programação | Python 3.12 | Melhor ecossistema para o caso de uso |
| 2 | Armazenamento dos dados | Google Sheets | Acesso online, familiar, gratuito |
| 3 | Autenticação com Google | Service Account | Automação sem login manual |
| 4 | Agendador | GitHub Actions | Gratuito, sem servidor próprio |
| 5 | Estação meteorológica | INMET A301 (Recife) | Estação automática oficial |
| 6 | Fonte de dados no MVP | Apenas INMET | APAC requer contato — fica para Fase 2 |
| 7 | Critérios de classificação | Adiado para Fase 2 | Ainda sem referência normativa definida |
| 8 | Granularidade dos dados | Diária (agregado de horários) | Relevante para registro de dia improdutivo |

---

## 10. Itens pendentes (a definir futuramente)

- [ ] **Critérios de classificação de dia improdutivo** — thresholds de precipitação (mm), velocidade de vento (m/s), duração da chuva etc. Referências a consultar: NBR 6118, condições contratuais das obras fiscalizadas
- [ ] **Conta GitHub** — confirmar se a empresa já possui conta
- [ ] **Conta Google Cloud** — necessário para criar Service Account e habilitar API Sheets
- [ ] **Contato com APAC** — enviar e-mail para monitoramento@apac.pe.gov.br solicitando acesso à API
- [ ] **Cadastro das obras ativas** — levantar endereços e coordenadas GPS das obras em andamento
- [ ] **Dashboard** — Google Looker Studio (Fase 4)
- [ ] **Relatório mensal automatizado** — integrar com fluxo de emissão de relatórios (Fase 5)

---

## 11. Roadmap de fases

| Fase | Descrição | Status |
|---|---|---|
| **MVP (Fase 1)** | Coleta INMET + registro Google Sheets + agendamento GitHub Actions | 🔨 Em desenvolvimento |
| **Fase 2** | Critérios de classificação de dia improdutivo | ⏳ Aguardando definição |
| **Fase 3** | Integração com APAC | ⏳ Aguardando contato com agência |
| **Fase 4** | Dashboard Google Looker Studio | ⏳ Planejada |
| **Fase 5** | Relatório mensal automatizado | ⏳ Planejada |

---

*Última atualização: 03/07/2026 — gerado por Antigravity com base nas decisões do chat de planejamento.*
