from coletor.classificador import avaliar_consenso

datas = ["2026-05-01", "2026-07-04", "2026-07-06"]

for d in datas:
    c, obs = avaliar_consenso([], [], "", d)
    print(f"{d} -> {c} ({obs})")
