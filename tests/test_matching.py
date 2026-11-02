import unittest

from matching import sequencia_aparece_em


class TestMatching(unittest.TestCase):

    def test_sequencia_exata(self):
        self.assertTrue(sequencia_aparece_em(['Bm', 'G', 'D', 'A'],
                                             ['Bm', 'G', 'D', 'A']))

    def test_ignora_caixa(self):
        self.assertTrue(sequencia_aparece_em(['Bm', 'G', 'D', 'A'],
                                             ['bm', 'g', 'd', 'a']))

    def test_sequencia_contigua_no_meio_da_cifra(self):
        self.assertTrue(sequencia_aparece_em(['G', 'D'],
                                             ['D', 'G', 'D']))

    def test_ordem_invertida_nao_casa(self):
        self.assertFalse(sequencia_aparece_em(['Bm', 'G'],
                                              ['G', 'Bm']))

    def test_preserva_repeticao_interna(self):
        self.assertTrue(sequencia_aparece_em(['C', 'C'],
                                             ['C', 'C']))
        self.assertFalse(sequencia_aparece_em(['C', 'C'],
                                              ['C']))

    def test_acorde_fora_da_sequencia_invalida(self):
        self.assertFalse(sequencia_aparece_em(['Bm', 'G'],
                                              ['Bm', 'G', 'A']))

    def test_repeticao_fora_do_bloco_continua_valida(self):
        self.assertTrue(sequencia_aparece_em(['Bm', 'G'],
                                             ['Bm', 'Bm', 'G']))

    def test_cifra_vazia_nao_casa(self):
        self.assertFalse(sequencia_aparece_em(['Bm', 'G'], []))


if __name__ == '__main__':
    unittest.main()
