import os
import tempfile
import unittest
from pathlib import Path

from sequencias_db import (SequenciaDuplicada, buscar_sequencia_por_acordes,
                           criar_sequencia, inicializar_banco,
                           listar_sequencias)


class TestSequenciasDb(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.banco = Path(self.tempdir.name) / 'sequencias.db'
        inicializar_banco(self.banco)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_seed_cria_as_seis_originais(self):
        sequencias = listar_sequencias(self.banco)
        self.assertEqual([seq['id'] for seq in sequencias], list(range(6)))
        self.assertEqual(sequencias[0]['nome'], 'Sequência de Bm')
        self.assertEqual(sequencias[0]['acordes'], ['Bm', 'G', 'D', 'A'])
        self.assertEqual(sequencias[5]['acordes'], ['C', 'C7', 'F', 'Fm'])

    def test_seed_e_idempotente(self):
        inicializar_banco(self.banco)
        self.assertEqual(len(listar_sequencias(self.banco)), 6)

    def test_cria_sequencia_sem_nome(self):
        sequencia = criar_sequencia(None, ['X', 'Y'], self.banco)
        self.assertEqual(sequencia['nome'], None)
        self.assertEqual(sequencia['acordes'], ['X', 'Y'])
        self.assertEqual(len(listar_sequencias(self.banco)), 7)

    def test_duplicata_ignora_caixa(self):
        criar_sequencia('Nova', ['X', 'Y'], self.banco)
        with self.assertRaises(SequenciaDuplicada):
            criar_sequencia('Outro nome', ['x', 'y'], self.banco)

    def test_busca_por_acordes_ignora_caixa(self):
        sequencia = buscar_sequencia_por_acordes(['bm', 'g', 'd', 'a'],
                                                 self.banco)
        self.assertIsNotNone(sequencia)
        self.assertEqual(sequencia['id'], 0)

    def test_busca_desconhecida_retorna_none(self):
        self.assertIsNone(buscar_sequencia_por_acordes(['X', 'Y'], self.banco))

    def test_persiste_entre_conexoes(self):
        criar_sequencia('Persistida', ['X', 'Y'], self.banco)
        sequencia = buscar_sequencia_por_acordes(['X', 'Y'], self.banco)
        self.assertEqual(sequencia['nome'], 'Persistida')

    def test_respeita_sequences_db(self):
        caminho_env = Path(self.tempdir.name) / 'via_env.db'
        antigo = os.environ.get('SEQUENCES_DB')
        os.environ['SEQUENCES_DB'] = str(caminho_env)
        try:
            inicializar_banco()
            self.assertTrue(caminho_env.exists())
            self.assertEqual(len(listar_sequencias()), 6)
        finally:
            if antigo is None:
                os.environ.pop('SEQUENCES_DB', None)
            else:
                os.environ['SEQUENCES_DB'] = antigo


if __name__ == '__main__':
    unittest.main()
