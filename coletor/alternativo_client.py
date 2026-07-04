import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import random

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

