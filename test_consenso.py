import unittest
from coletor.classificador import avaliar_consenso, classificar_noticias

class TestConsenso(unittest.TestCase):
    def test_classificar_noticias(self):
        self.assertTrue(classificar_noticias("G1 PE: Alagamento em Recife hoje."))
        self.assertTrue(classificar_noticias("Temporal atinge o sertão."))
        self.assertFalse(classificar_noticias("Dia ensolarado."))
        self.assertTrue(classificar_noticias("Defesa civil em alerta para deslizamento."))

    def test_consenso_ambos_produtivos_com_noticia_ruim(self):
        # INMET e APAC vazios -> PENDENTE, mas notícia tem alerta -> PRODUTIVO_RESSALVA
        class_final, obs_final = avaliar_consenso([], [], "Alerta de temporal na região", "2026-07-03")
        self.assertEqual(class_final, "PRODUTIVO_RESSALVA")
        self.assertIn("Notícias: Alerta de temporal na região", obs_final)

    def test_consenso_inmet_improdutivo(self):
        # INMET com chuva pesada, APAC vazio
        reg_inmet = [{
            "HR_MEDIDA": "1400", # 11:00 BRT (Manhã)
            "CHUVA": "10.0",
            "VEN_RAJ": "0"
        }]
        class_final, obs = avaliar_consenso(reg_inmet, [], "Tudo bem", "2026-07-03")
        self.assertEqual(class_final, "IMPRODUTIVO_PARCIAL") # Manhã improdutiva, tarde normal

    def test_consenso_apac_improdutivo(self):
        # INMET vazio, APAC com chuva pesada
        reg_apac = [{
            "HR_MEDIDA": "1400", # 11:00 BRT (Manhã)
            "CHUVA": "15.0",
            "VEN_RAJ": "0"
        }]
        class_final, obs = avaliar_consenso([], reg_apac, "Sem problemas", "2026-07-03")
        self.assertEqual(class_final, "IMPRODUTIVO_PARCIAL")

if __name__ == '__main__':
    unittest.main()
