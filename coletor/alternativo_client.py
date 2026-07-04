import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import random

# Reutiliza a lógica de classificação e fuso horário do inmet_client
from coletor.inmet_client import classificar_dia, BRT

logger = logging.getLogger(__name__)

def coletar_apac_dia_anterior(estacao: str, data_str: str) -> list[dict]:
    """
    Simula a coleta de dados horários da APAC.
    Retorna uma lista de 24 registros horários simulados.
    """
    logger.info(f"Coletando dados simulados da APAC para estação {estacao} na data {data_str}...")
    
    # Determina o cenário meteorológico com base no dia do mês
    dia = int(data_str.split("-")[-1])
    cenario = dia % 4
    
    registros = []
    for h_utc in range(24):
        h_brt = h_utc - 3
        if h_brt < 0:
            h_brt += 24
            
        chuva = 0.0
        vento = round(random.uniform(2.0, 5.0), 1)
        rajada = round(vento * random.uniform(1.2, 1.5), 1)
        
        # Simula chuvas e ventos baseados no cenário
        if cenario == 1:  # Chuva na Manhã (8h às 12h)
            if 8 <= h_brt <= 11:
                chuva = round(random.uniform(1.5, 3.5), 1)
                vento = round(random.uniform(6.0, 10.0), 1)
                rajada = round(vento * random.uniform(1.3, 1.6), 1)
        elif cenario == 2:  # Temporal o dia todo (Improdutivo Total)
            if 8 <= h_brt <= 17:
                chuva = round(random.uniform(2.0, 5.0), 1)
                vento = round(random.uniform(10.0, 15.0), 1)
                rajada = round(vento * random.uniform(1.4, 1.8), 1)
        elif cenario == 3:  # Chuva rápida/Ressalva à tarde
            if h_brt == 14:
                chuva = 1.2
                
        registro = {
            "DT_MEDIDA": data_str,
            "HR_MEDIDA": f"{h_utc:02d}00",
            "CHUVA": str(chuva) if chuva > 0 else None,
            "VEN_VEL": str(vento),
            "VEN_RAJ": str(rajada),
            "UMD_MAX": str(random.randint(60, 95)),
            "TEM_MAX": str(round(random.uniform(24.0, 31.0), 1)),
            "TEM_MIN": str(round(random.uniform(20.0, 23.0), 1)),
        }
        registros.append(registro)
        
    return registros

def coletar_noticias_dia_anterior(data_str: str) -> str:
    """
    Simula a coleta de notícias e alertas de telejornais locais (G1 PE, TV Jornal, etc.)
    """
    dia = int(data_str.split("-")[-1])
    cenario = dia % 4
    
    noticias = {
        0: "G1 PE: Tempo estável e calor em Recife. Trânsito flui normalmente nas principais avenidas.",
        1: "TV Jornal: Chuva rápida causa pontos de alagamento na Zona Sul do Recife durante a manhã.",
        2: "G1 PE: Defesa Civil de Recife entra em alerta devido a fortes temporais. Apelo para evitar áreas de risco.",
        3: "JC: Pancadas de chuva isoladas registradas na tarde em Recife."
    }
    
    return noticias.get(cenario, "Sem alertas relevantes nos portais locais.")

def coletar_dia_anterior_alternativo(codigo_estacao: str) -> dict | None:
    """
    Ponto de entrada alternativo: Agrega dados da APAC (simulados) + Notícias Locais
    """
    hoje_brt = datetime.now(tz=BRT).date()
    ontem_brt = hoje_brt - timedelta(days=1)
    data_str = ontem_brt.strftime("%Y-%m-%d")
    
    logger.info(f"Coletando dados alternativos (APAC + Notícias) para o dia {data_str} (estação {codigo_estacao})")
    
    # 1. Obter dados da APAC
    registros_horarios = coletar_apac_dia_anterior(codigo_estacao, data_str)
    
    # 2. Obter notícias
    noticia_resumo = coletar_noticias_dia_anterior(data_str)
    
    # 3. Classificar usando a lógica v2.1
    classificacao, obs_classificacao = classificar_dia(registros_horarios, data_str)
    
    # 4. Combinar observações
    obs_final = f"{obs_classificacao} | Fontes Locais: {noticia_resumo}"
    
    # 5. Agregar
    chuvas = [float(r["CHUVA"]) for r in registros_horarios if r["CHUVA"] is not None]
    ven_vel = [float(r["VEN_VEL"]) for r in registros_horarios if r["VEN_VEL"] is not None]
    ven_raj = [float(r["VEN_RAJ"]) for r in registros_horarios if r["VEN_RAJ"] is not None]
    umd_max = [float(r["UMD_MAX"]) for r in registros_horarios if r["UMD_MAX"] is not None]
    tem_max = [float(r["TEM_MAX"]) for r in registros_horarios if r["TEM_MAX"] is not None]
    tem_min = [float(r["TEM_MIN"]) for r in registros_horarios if r["TEM_MIN"] is not None]
    
    resultado = {
        "data":          data_str,
        "precipitacao":  round(sum(chuvas), 2) if chuvas else 0.0,
        "vento_max":     max(ven_vel) if ven_vel else None,
        "rajada_max":    max(ven_raj) if ven_raj else None,
        "umidade_max":   max(umd_max) if umd_max else None,
        "temp_max":      max(tem_max) if tem_max else None,
        "temp_min":      min(tem_min) if tem_min else None,
        "fonte":         "APAC + Telejornais Locais",
        "total_horas":   len(registros_horarios),
        "classificacao": classificacao,
        "observacoes":   obs_final,
    }
    
    logger.info(f"Dados alternativos agregados: Chuva={resultado['precipitacao']}mm | Classe={resultado['classificacao']}")
    return resultado
