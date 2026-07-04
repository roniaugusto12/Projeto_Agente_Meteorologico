"""
classificador.py — Motor de Consenso para Classificação de Dias
Avalia dados do INMET, APAC e Notícias Locais para definir a produtividade.
"""

import logging
from datetime import datetime
import holidays
from config import (
    HORA_INICIO_MANHA, HORA_FIM_MANHA, HORA_INICIO_TARDE,
    HORA_FIM_TARDE_NORMAL, HORA_FIM_TARDE_SEXTA,
    CHUVA_HORA_ADVERSA, CHUVA_HORA_ATENCAO, RAJADA_IMPRODUTIVO, RAJADA_ATENCAO,
    CHUVA_MANHA_IMPRODUTIVO, CHUVA_MANHA_PARCIAL, CHUVA_MANHA_RESSALVA,
    CHUVA_TARDE_IMPRODUTIVO, CHUVA_TARDE_PARCIAL, CHUVA_TARDE_RESSALVA,
    CHUVA_SEXTA_IMPRODUTIVO, CHUVA_SEXTA_PARCIAL, CHUVA_SEXTA_RESSALVA,
    HORAS_IMP_MANHA, HORAS_IMP_TARDE_NORMAL, HORAS_IMP_TARDE_SEXTA,
    CHUVA_DIRIGIDA_MM, CHUVA_DIRIGIDA_VENTO,
)

logger = logging.getLogger(__name__)

def _safe_float(valor) -> float | None:
    try:
        if valor is None or valor == "" or valor == "null":
            return None
        return float(valor)
    except (ValueError, TypeError):
        return None

def obter_hora_brt(registro: dict) -> int | None:
    hr_str = registro.get("HR_MEDIDA")
    if not hr_str:
        return None
    hr_str = hr_str.replace(":", "")
    try:
        hr_utc = int(hr_str) // 100
        return hr_utc - 3
    except (ValueError, TypeError):
        return None

def classificar_fonte(registros_horarios: list[dict], data_referencia: str) -> tuple[str, str]:
    """Classifica o dia baseado em UMA fonte (INMET ou APAC)."""
    if not registros_horarios:
        return "PENDENTE", "Sem dados horários"

    try:
        dt = datetime.strptime(data_referencia, "%Y-%m-%d")
        dia_semana = dt.weekday()
    except Exception:
        dia_semana = 0

    dias_nomes = ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"]
    dia_nome = dias_nomes[dia_semana] if dia_semana < 7 else "DIA"

    hora_fim_tarde = HORA_FIM_TARDE_SEXTA if dia_semana == 4 else HORA_FIM_TARDE_NORMAL
    horas_imp_tarde = HORAS_IMP_TARDE_SEXTA if dia_semana == 4 else HORAS_IMP_TARDE_NORMAL
    chuva_tarde_imp = CHUVA_SEXTA_IMPRODUTIVO if dia_semana == 4 else CHUVA_TARDE_IMPRODUTIVO
    chuva_tarde_parcial = CHUVA_SEXTA_PARCIAL if dia_semana == 4 else CHUVA_TARDE_PARCIAL
    chuva_tarde_ressalva = CHUVA_SEXTA_RESSALVA if dia_semana == 4 else CHUVA_TARDE_RESSALVA

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

            if chuva >= CHUVA_HORA_ADVERSA or rajada >= RAJADA_IMPRODUTIVO:
                horas_adversas += 1
            elif chuva >= CHUVA_HORA_ATENCAO or rajada >= RAJADA_ATENCAO:
                horas_atencao += 1

        if chuva_total >= CHUVA_DIRIGIDA_MM and rajada_max >= CHUVA_DIRIGIDA_VENTO:
            return "IMPRODUTIVO", f"chuva_dirigida({chuva_total:.1f}mm, {rajada_max:.1f}m/s)"

        if horas_adversas >= horas_imp_req or chuva_total >= chuva_imp:
            return "IMPRODUTIVO", f"improdutivo({horas_adversas}h_adv, {chuva_total:.1f}mm)"

        if horas_adversas >= 1 or chuva_total >= chuva_parcial:
            return "PARCIAL", f"parcial({horas_adversas}h_adv, {chuva_total:.1f}mm)"

        if horas_atencao >= 1 or chuva_total >= chuva_ressalva:
            return "RESSALVA", f"ressalva({horas_atencao}h_aten, {chuva_total:.1f}mm)"

        return "NORMAL", "normal"

    class_manha, desc_manha = analisar_periodo(reg_manha, CHUVA_MANHA_IMPRODUTIVO, CHUVA_MANHA_PARCIAL, CHUVA_MANHA_RESSALVA, HORAS_IMP_MANHA)
    class_tarde, desc_tarde = analisar_periodo(reg_tarde, chuva_tarde_imp, chuva_tarde_parcial, chuva_tarde_ressalva, horas_imp_tarde)

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

def classificar_noticias(noticia: str) -> bool:
    """Verifica se há palavras-chave de risco na notícia."""
    if not noticia:
        return False
    palavras_chave = [
        "alagamento", "temporal", "queda de árvore", "deslizamento", 
        "enchente", "alerta", "chuva"
    ]
    noticia_lower = noticia.lower()
    for p in palavras_chave:
        if p in noticia_lower:
            return True
    return False

def avaliar_consenso(registros_inmet: list[dict], registros_apac: list[dict], noticia: str, data_referencia: str) -> tuple[str, str]:
    """
    Avalia INMET e APAC. O pior caso prevalece.
    Se a base (INMET/APAC) der PRODUTIVO, mas houver palavra-chave na notícia,
    rebaixa para RESSALVA, mantendo os dados técnicos.
    Feriados e finais de semana são filtrados imediatamente.
    """
    try:
        dt = datetime.strptime(data_referencia, "%Y-%m-%d")
        
        # 1. Checagem de Final de Semana
        if dt.weekday() >= 5: # 5 = Sábado, 6 = Domingo
            return "FINAL DE SEMANA", "Sem expediente"
        
        # 2. Checagem de Feriado (Nacional e PE)
        br_holidays = holidays.BR(state='PE')
        if dt.date() in br_holidays:
            nome_feriado = br_holidays.get(dt.date())
            return "FERIADO", f"{nome_feriado}"
    except Exception as e:
        logger.error(f"Erro ao avaliar feriado/fim de semana: {e}")
        pass
    
    class_inmet, obs_inmet = classificar_fonte(registros_inmet, data_referencia)
    class_apac, obs_apac = classificar_fonte(registros_apac, data_referencia)
    tem_risco_noticia = classificar_noticias(noticia)

    hierarquia = {
        "IMPRODUTIVO_TOTAL": 4,
        "IMPRODUTIVO_PARCIAL": 3,
        "PRODUTIVO_RESSALVA": 2,
        "PRODUTIVO": 1,
        "PENDENTE": 0
    }

    nivel_inmet = hierarquia.get(class_inmet, 0)
    nivel_apac = hierarquia.get(class_apac, 0)

    # O pior caso entre INMET e APAC prevalece
    if nivel_inmet >= nivel_apac:
        class_final = class_inmet
    else:
        class_final = class_apac

    # Se a base for produtiva, mas a notícia alertar risco -> RESSALVA
    if class_final == "PRODUTIVO" and tem_risco_noticia:
        class_final = "PRODUTIVO_RESSALVA"
    
    if class_final == "PENDENTE" and tem_risco_noticia:
        class_final = "PRODUTIVO_RESSALVA" 

    obs_final = f"INMET: {obs_inmet} | APAC: {obs_apac} | Notícias: {noticia}"
    
    return class_final, obs_final
