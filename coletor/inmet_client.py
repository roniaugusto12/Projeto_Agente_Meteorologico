"""
inmet_client.py — Coleta e agregação de dados meteorológicos da API do INMET
Estação de referência: A301 (Recife-PE)

A API pública do INMET retorna dados horários em UTC.
Este módulo:
  1. Consulta os dados horários do dia anterior
  2. Converte os horários de UTC para BRT (UTC-3)
  3. Agrega os dados para totais/máximos/mínimos diários
"""

import requests
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from config import (
    INMET_API_BASE,
    ESTACAO_PADRAO,
    TIMEZONE_BRT,
    # Períodos
    HORA_INICIO_MANHA,
    HORA_FIM_MANHA,
    HORA_INICIO_TARDE,
    HORA_FIM_TARDE_NORMAL,
    HORA_FIM_TARDE_SEXTA,
    # Thresholds horários
    CHUVA_HORA_ADVERSA,
    CHUVA_HORA_ATENCAO,
    RAJADA_IMPRODUTIVO,
    RAJADA_ATENCAO,
    # Thresholds período
    CHUVA_MANHA_IMPRODUTIVO,
    CHUVA_MANHA_PARCIAL,
    CHUVA_MANHA_RESSALVA,
    CHUVA_TARDE_IMPRODUTIVO,
    CHUVA_TARDE_PARCIAL,
    CHUVA_TARDE_RESSALVA,
    CHUVA_SEXTA_IMPRODUTIVO,
    CHUVA_SEXTA_PARCIAL,
    CHUVA_SEXTA_RESSALVA,
    # Mínimo horas
    HORAS_IMP_MANHA,
    HORAS_IMP_TARDE_NORMAL,
    HORAS_IMP_TARDE_SEXTA,
    # Chuva dirigida
    CHUVA_DIRIGIDA_MM,
    CHUVA_DIRIGIDA_VENTO,
)

logger = logging.getLogger(__name__)

# Fuso horário BRT
BRT = ZoneInfo(TIMEZONE_BRT)
UTC = ZoneInfo("UTC")


def _safe_float(valor) -> float | None:
    """Converte um valor para float, retornando None se inválido."""
    try:
        if valor is None or valor == "" or valor == "null":
            return None
        return float(valor)
    except (ValueError, TypeError):
        return None


def obter_hora_brt(registro: dict) -> int | None:
    """Extrai a hora e converte de UTC para BRT (UTC-3)."""
    hr_str = registro.get("HR_MEDIDA")
    if not hr_str:
        return None
    hr_str = hr_str.replace(":", "")  # remove colon if present (e.g. "12:00" -> "1200")
    try:
        hr_utc = int(hr_str) // 100  # e.g. 1200 -> 12
        return hr_utc - 3
    except (ValueError, TypeError):
        return None


def classificar_dia(registros_horarios: list[dict], data_referencia: str) -> tuple[str, str]:
    """
    Classifica o dia de trabalho como produtivo ou improdutivo com base nos critérios v2.1.
    Retorna (classificação, observações).
    """
    if not registros_horarios:
        return "PENDENTE", "Sem dados horários"

    try:
        dt = datetime.strptime(data_referencia, "%Y-%m-%d")
        dia_semana = dt.weekday()  # 0=Seg, 4=Sex, etc.
    except Exception:
        dia_semana = 0  # fallback

    dias_nomes = ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"]
    dia_nome = dias_nomes[dia_semana] if dia_semana < 7 else "DIA"

    # Define a hora final da tarde com base no dia da semana
    hora_fim_tarde = HORA_FIM_TARDE_SEXTA if dia_semana == 4 else HORA_FIM_TARDE_NORMAL
    horas_imp_tarde = HORAS_IMP_TARDE_SEXTA if dia_semana == 4 else HORAS_IMP_TARDE_NORMAL
    chuva_tarde_imp = CHUVA_SEXTA_IMPRODUTIVO if dia_semana == 4 else CHUVA_TARDE_IMPRODUTIVO
    chuva_tarde_parcial = CHUVA_SEXTA_PARCIAL if dia_semana == 4 else CHUVA_TARDE_PARCIAL
    chuva_tarde_ressalva = CHUVA_SEXTA_RESSALVA if dia_semana == 4 else CHUVA_TARDE_RESSALVA

    # Separa os registros por período
    reg_manha = []
    reg_tarde = []
    
    for r in registros_horarios:
        hr = obter_hora_brt(r)
        if hr is None:
            continue
        if HORA_INICIO_MANHA <= hr <= HORA_FIM_MANHA:
            reg_manha.append(r)
        elif HORA_INICIO_TARDE <= hr <= hora_fim_tarde:
            reg_tarde.append(r)

    def analisar_periodo(registros, chuva_imp, chuva_parcial, chuva_ressalva, horas_imp_req):
        if not registros:
            return "NORMAL", "Sem dados"

        chuva_total = 0.0
        rajada_max = 0.0
        horas_adversas = 0
        horas_atencao = 0

        for r in registros:
            chuva = _safe_float(r.get("CHUVA")) or 0.0
            rajada = _safe_float(r.get("VEN_RAJ")) or 0.0
            
            chuva_total += chuva
            if rajada > rajada_max:
                rajada_max = rajada

            # Classifica a hora
            if chuva >= CHUVA_HORA_ADVERSA or rajada >= RAJADA_IMPRODUTIVO:
                horas_adversas += 1
            elif chuva >= CHUVA_HORA_ATENCAO or rajada >= RAJADA_ATENCAO:
                horas_atencao += 1

        # Critério combinado (chuva dirigida)
        if chuva_total >= CHUVA_DIRIGIDA_MM and rajada_max >= CHUVA_DIRIGIDA_VENTO:
            return "IMPRODUTIVO", f"chuva_dirigida({chuva_total:.1f}mm, {rajada_max:.1f}m/s)"

        if horas_adversas >= horas_imp_req or chuva_total >= chuva_imp:
            return "IMPRODUTIVO", f"improdutivo({horas_adversas}h_adv, {chuva_total:.1f}mm)"

        if horas_adversas >= 1 or chuva_total >= chuva_parcial:
            return "PARCIAL", f"parcial({horas_adversas}h_adv, {chuva_total:.1f}mm)"

        if horas_atencao >= 1 or chuva_total >= chuva_ressalva:
            return "RESSALVA", f"ressalva({horas_atencao}h_aten, {chuva_total:.1f}mm)"

        return "NORMAL", "normal"

    class_manha, desc_manha = analisar_periodo(
        reg_manha, 
        CHUVA_MANHA_IMPRODUTIVO, 
        CHUVA_MANHA_PARCIAL, 
        CHUVA_MANHA_RESSALVA, 
        HORAS_IMP_MANHA
    )

    class_tarde, desc_tarde = analisar_periodo(
        reg_tarde, 
        chuva_tarde_imp, 
        chuva_tarde_parcial, 
        chuva_tarde_ressalva, 
        horas_imp_tarde
    )

    # Combinação para determinar a classificação final do dia
    if class_manha == "IMPRODUTIVO" and class_tarde == "IMPRODUTIVO":
        class_dia = "IMPRODUTIVO_TOTAL"
    elif class_manha == "IMPRODUTIVO" and class_tarde == "PARCIAL":
        class_dia = "IMPRODUTIVO_TOTAL"
    elif class_manha == "PARCIAL" and class_tarde == "IMPRODUTIVO":
        class_dia = "IMPRODUTIVO_TOTAL"
    elif class_manha == "IMPRODUTIVO" or class_tarde == "IMPRODUTIVO":
        class_dia = "IMPRODUTIVO_PARCIAL"
    elif class_manha == "PARCIAL" and class_tarde == "PARCIAL":
        class_dia = "IMPRODUTIVO_PARCIAL"
    elif class_manha == "PARCIAL" or class_tarde == "PARCIAL":
        class_dia = "PRODUTIVO_RESSALVA"
    elif class_manha == "RESSALVA" or class_tarde == "RESSALVA":
        class_dia = "PRODUTIVO_RESSALVA"
    else:
        class_dia = "PRODUTIVO"

    obs = f"[{dia_nome}] MANHA_{class_manha}({desc_manha}) | TARDE_{class_tarde}({desc_tarde})"
    return class_dia, obs


def buscar_dados_horarios(data: str, codigo_estacao: str = ESTACAO_PADRAO) -> list[dict]:
    """
    Busca os dados horários de uma estação INMET para uma data específica.

    Args:
        data: Data no formato 'YYYY-MM-DD' (horário BRT — o dia que queremos registrar)
        codigo_estacao: Código da estação INMET (padrão: A301 — Recife)

    Returns:
        Lista de dicionários com os dados horários brutos da API.
        Retorna lista vazia em caso de erro.
    """
    # A API recebe datas no formato YYYY-MM-DD
    url = f"{INMET_API_BASE}/estacao/{data}/{data}/{codigo_estacao}"
    logger.info(f"Consultando INMET: {url}")

    try:
        resposta = requests.get(url, timeout=30)
        resposta.raise_for_status()
        dados = resposta.json()

        if not dados:
            logger.warning(f"API INMET retornou dados vazios para {data} / {codigo_estacao}")
            return []

        logger.info(f"Recebidos {len(dados)} registros horários da estação {codigo_estacao}")
        return dados

    except requests.exceptions.Timeout:
        logger.error("Timeout ao consultar a API do INMET.")
        return []
    except requests.exceptions.HTTPError as e:
        logger.error(f"Erro HTTP ao consultar INMET: {e}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de conexão com INMET: {e}")
        return []
    except ValueError:
        logger.error("Resposta da API INMET não é um JSON válido.")
        return []


def agregar_dados_diarios(registros_horarios: list[dict], data_referencia: str) -> dict | None:
    """
    Agrega os registros horários em um resumo diário.

    Agregações:
        - CHUVA    → soma
        - VEN_VEL  → máximo
        - VEN_RAJ  → máximo
        - UMD_MAX  → máximo
        - TEM_MAX  → máximo
        - TEM_MIN  → mínimo

    Args:
        registros_horarios: Lista de dicts retornados pela API INMET.
        data_referencia: Data no formato 'YYYY-MM-DD' para validação.

    Returns:
        Dicionário com os valores agregados, ou None se não houver dados válidos.
    """
    if not registros_horarios:
        return None

    chuvas    = []
    ven_vel   = []
    ven_raj   = []
    umd_max   = []
    tem_max   = []
    tem_min   = []

    for registro in registros_horarios:
        chuvas.append(_safe_float(registro.get("CHUVA")))
        ven_vel.append(_safe_float(registro.get("VEN_VEL")))
        ven_raj.append(_safe_float(registro.get("VEN_RAJ")))
        umd_max.append(_safe_float(registro.get("UMD_MAX")))
        tem_max.append(_safe_float(registro.get("TEM_MAX")))
        tem_min.append(_safe_float(registro.get("TEM_MIN")))

    def soma_validos(valores):
        validos = [v for v in valores if v is not None]
        return round(sum(validos), 2) if validos else None

    def max_validos(valores):
        validos = [v for v in valores if v is not None]
        return round(max(validos), 2) if validos else None

    def min_validos(valores):
        validos = [v for v in valores if v is not None]
        return round(min(validos), 2) if validos else None

    classificacao, observacoes = classificar_dia(registros_horarios, data_referencia)

    resultado = {
        "data":          data_referencia,
        "precipitacao":  soma_validos(chuvas),
        "vento_max":     max_validos(ven_vel),
        "rajada_max":    max_validos(ven_raj),
        "umidade_max":   max_validos(umd_max),
        "temp_max":      max_validos(tem_max),
        "temp_min":      min_validos(tem_min),
        "fonte":         "INMET",
        "total_horas":   len(registros_horarios),
        "classificacao": classificacao,
        "observacoes":   observacoes,
    }

    logger.info(
        f"Dados agregados para {data_referencia}: "
        f"Chuva={resultado['precipitacao']}mm | "
        f"Vento={resultado['vento_max']}m/s | "
        f"Rajada={resultado['rajada_max']}m/s | "
        f"Classe={resultado['classificacao']}"
    )
    return resultado


def coletar_dia_anterior(codigo_estacao: str = ESTACAO_PADRAO) -> dict | None:
    """
    Coleta e agrega os dados meteorológicos do dia anterior em BRT.

    Esta é a função principal chamada pelo agendador diário.
    O agente roda às 06:00 BRT → coleta dados do dia anterior (completo).

    Args:
        codigo_estacao: Código da estação INMET (padrão: A301)

    Returns:
        Dicionário com dados agregados do dia, ou None em caso de falha.
    """
    hoje_brt = datetime.now(tz=BRT).date()
    ontem_brt = hoje_brt - timedelta(days=1)
    data_str = ontem_brt.strftime("%Y-%m-%d")

    logger.info(f"Coletando dados do dia: {data_str} (estação {codigo_estacao})")

    registros = buscar_dados_horarios(data_str, codigo_estacao)
    return agregar_dados_diarios(registros, data_str)
