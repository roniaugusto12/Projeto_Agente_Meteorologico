import sys
import os

# Adiciona o diretório atual ao path para importarmos coletor
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from coletor.inmet_client import classificar_dia

def testar_caso(nome, registros, data):
    classe, obs = classificar_dia(registros, data)
    print(f"--- Caso: {nome} ({data}) ---")
    print(f"Classe: {classe}")
    print(f"Obs: {obs}")
    print()
    return classe, obs

# Scenarios (Note: HR_MEDIDA is in UTC, so we map BRT hours + 3 to get UTC hours)
# 1. Dia normal (Quinta-feira 2026-07-02) - Sem chuvas ou vento forte
reg_normal = [
    {"HR_MEDIDA": f"{h:02d}00", "CHUVA": "0.0", "VEN_RAJ": "2.0"} for h in range(24)
]
testar_caso("Dia Normal (Quinta)", reg_normal, "2026-07-02")

# 2. Chuva apenas na madrugada (03:00 BRT = 06:00 UTC) - Deve ser classificado como PRODUTIVO
reg_chuva_madrugada = [
    {"HR_MEDIDA": f"{h:02d}00", "CHUVA": "15.0" if h == 6 else "0.0", "VEN_RAJ": "1.0"} for h in range(24)
]
testar_caso("Chuva na Madrugada (Quinta)", reg_chuva_madrugada, "2026-07-02")

# 3. Chuva na Manhã BRT (08h, 09h, 10h BRT = 11h, 12h, 13h UTC) - 3 horas adversas -> IMPRODUTIVO_PARCIAL (pois tarde é normal)
reg_chuva_manha = [
    {"HR_MEDIDA": f"{h:02d}00", "CHUVA": "2.0" if h in [11, 12, 13] else "0.0", "VEN_RAJ": "2.0"} for h in range(24)
]
testar_caso("Chuva na Manhã (Quinta)", reg_chuva_manha, "2026-07-02")

# 4. Chuva dirigida na Manhã (Chuva 5mm + Rajada 8m/s na mesma hora, ex: 11 UTC = 08 BRT -> IMPRODUTIVO_PARCIAL)
reg_chuva_dirigida = [
    {"HR_MEDIDA": "1100", "CHUVA": "5.0", "VEN_RAJ": "8.0"}
]
testar_caso("Chuva Dirigida (Manhã)", reg_chuva_dirigida, "2026-07-02")

# 5. Sexta-feira com tarde de 2 horas adversas (14h, 15h BRT = 17h, 18h UTC) -> IMPRODUTIVO_PARCIAL (se manhã normal)
# Se ambas as horas da tarde de sexta forem adversas, a tarde fica IMPRODUTIVA.
reg_sexta_tarde = [
    {"HR_MEDIDA": "1700", "CHUVA": "1.0", "VEN_RAJ": "2.0"},
    {"HR_MEDIDA": "1800", "CHUVA": "1.5", "VEN_RAJ": "3.0"}
]
testar_caso("Tarde de Sexta-feira", reg_sexta_tarde, "2026-07-03")

# 6. Manhã Improdutiva (11h, 12h, 13h UTC) + Tarde Improdutiva (17h, 18h UTC) -> IMPRODUTIVO_TOTAL
reg_total_improdutivo = [
    {"HR_MEDIDA": f"{h:02d}00", "CHUVA": "2.0" if h in [11, 12, 13, 17, 18] else "0.0", "VEN_RAJ": "2.0"} for h in range(24)
]
testar_caso("Dia Inteiro Improdutivo (Quinta)", reg_total_improdutivo, "2026-07-02")
