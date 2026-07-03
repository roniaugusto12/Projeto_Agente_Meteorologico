# Teste unitário manual dos critérios de classificação
import sys
sys.path.append(r"c:\Users\Roni\Desktop\Tecomat\programacao\projeto 01")

from coletor.inmet_client import classificar_dia

testes = [
    # (Chuva, Vento, Rajada, EsperadoClas, ContemTexto)
    (0.0, 2.0, 5.0, "PRODUTIVO", "favoráveis"),
    (1.5, 9.9, 13.9, "PRODUTIVO", "favoráveis"),
    (2.0, 1.0, 3.0, "IMPRODUTIVO", "Chuva de 2.0mm"),
    (5.5, 2.0, 4.0, "IMPRODUTIVO", "Chuva de 5.5mm"),
    (0.0, 10.0, 5.0, "IMPRODUTIVO", "Vento de 10.0m/s"),
    (0.0, 5.0, 14.0, "IMPRODUTIVO", "Rajada de 14.0m/s"),
    (3.0, 11.0, 15.0, "IMPRODUTIVO", "Chuva"), # múltiplos motivos
]

sucesso = True
for i, (chuva, vento, rajada, exp_clas, exp_texto) in enumerate(testes):
    res_clas, res_texto = classificar_dia(chuva, vento, rajada)
    if res_clas != exp_clas or exp_texto not in res_texto:
        print(f"[ERRO] Teste {i} falhou! Entrada: Chuva={chuva}, Vento={vento}, Rajada={rajada}. Esperado: {exp_clas} / '{exp_texto}'. Obtido: {res_clas} / '{res_texto}'")
        sucesso = False
    else:
        print(f"[OK] Teste {i} ok: {res_clas} -> {res_texto}")

if sucesso:
    print("\nTODOS OS TESTES PASSARAM COM SUCESSO!")
