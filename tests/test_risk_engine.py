"""Testes do motor de risco (calcular_risco). Sem acesso à internet.

Rodar:  python -m unittest discover -s tests -v
"""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import risk_engine
from risk_engine import calcular_risco, _parece_endereco

ASSINATURA = "5" * 88
ENDERECO = "BbTBNyukp6xP4JfdD3Mth99ufCWoCB55zZcTeNPgu3QQ"


class CenariosDeDemonstracaoTest(unittest.TestCase):
    def test_status_e_faixa_de_score(self):
        faixas = {"tx_001": ("Green", 0, 30), "tx_002": ("Yellow", 31, 70), "tx_003": ("Red", 71, 100)}
        for chave, (status, minimo, maximo) in faixas.items():
            r = calcular_risco(chave)
            self.assertEqual(r["status"], status, chave)
            self.assertTrue(minimo <= r["score"] <= maximo, chave)

    def test_ignora_espacos_e_maiusculas(self):
        self.assertEqual(calcular_risco("  TX_003 ")["status"], "Red")

    def test_todo_cenario_tem_motivos_com_nivel_valido(self):
        for chave in ("tx_001", "tx_002", "tx_003"):
            motivos = calcular_risco(chave)["motivos"]
            self.assertTrue(motivos, chave)
            for m in motivos:
                self.assertIn(m["nivel"], {"alto", "medio", "baixo", "ok"})
                self.assertTrue(m["texto"])

    def test_cenario_vermelho_nao_tem_motivo_ok(self):
        niveis = {m["nivel"] for m in calcular_risco("tx_003")["motivos"]}
        self.assertNotIn("ok", niveis)


class EntradasInvalidasTest(unittest.TestCase):
    def assert_desconhecida(self, r):
        self.assertTrue(r.get("desconhecida"))
        self.assertEqual(r["status"], "Yellow")  # na dúvida, nunca verde
        self.assertNotIn("site", r)

    def test_texto_qualquer(self):
        self.assert_desconhecida(calcular_risco("abc"))

    def test_vazio(self):
        self.assert_desconhecida(calcular_risco(""))

    def test_endereco_de_carteira_orienta_a_colar_a_signature(self):
        r = calcular_risco(ENDERECO)
        self.assert_desconhecida(r)
        self.assertIn("Signature", r["mensagem"])

    def test_parece_endereco(self):
        self.assertTrue(_parece_endereco(ENDERECO))
        self.assertFalse(_parece_endereco("0" + ENDERECO[1:]))  # '0' não é base58
        self.assertFalse(_parece_endereco("abc"))


class SignatureReal(unittest.TestCase):
    def test_usa_resultado_da_analise(self):
        esperado = {"status": "Green", "score": 5}
        with mock.patch("solana_rpc.analisar", return_value=esperado):
            self.assertEqual(calcular_risco(ASSINATURA), esperado)

    def test_rede_fora_do_ar_nao_vira_verde_nem_quebra(self):
        with mock.patch("solana_rpc.analisar", side_effect=RuntimeError("timeout")):
            r = calcular_risco(ASSINATURA)
        self.assertTrue(r.get("desconhecida"))
        self.assertEqual(r["status"], "Yellow")
        self.assertIn("timeout", r["mensagem"])

    def test_transacao_nao_encontrada(self):
        with mock.patch("solana_rpc.analisar", return_value=None):
            r = calcular_risco(ASSINATURA)
        self.assertTrue(r.get("desconhecida"))
        self.assertIn("não encontrada", r["mensagem"])


if __name__ == "__main__":
    unittest.main()
