import json
import os
import sqlite3
import tempfile
import unittest

_TEMP_DIR = tempfile.TemporaryDirectory()
os.environ['SEQUENCES_DB'] = os.path.join(_TEMP_DIR.name, 'api.db')

import main  # noqa: E402


def tearDownModule():
    _TEMP_DIR.cleanup()


class TestApi(unittest.TestCase):

    def setUp(self):
        with sqlite3.connect(os.environ['SEQUENCES_DB']) as conn:
            conn.execute('DELETE FROM sequencias WHERE id > 5')
        self.client = main.app.test_client()

    def _json(self, response):
        return json.loads(response.get_data(as_text=True))

    def test_lista_as_seis_originais(self):
        response = self.client.get('/sequencias')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.content_type)

        sequencias = self._json(response)
        self.assertEqual([seq['id'] for seq in sequencias], list(range(6)))
        self.assertEqual(set(sequencias[0].keys()),
                         {'id', 'nome', 'acordes', 'criado_em'})

    def test_cria_sequencia_com_nome(self):
        response = self.client.post('/sequencias', json={
            'nome': 'Nova', 'acordes': ['X', 'Y']
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self._json(response)['nome'], 'Nova')
        self.assertEqual(len(self._json(self.client.get('/sequencias'))), 7)

    def test_cria_sequencia_sem_nome(self):
        response = self.client.post('/sequencias', json={
            'acordes': ['X', 'Y']
        })
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(self._json(response)['nome'])

    def test_nome_vazio_fica_nulo(self):
        response = self.client.post('/sequencias', json={
            'nome': '   ', 'acordes': ['X', 'Y']
        })
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(self._json(response)['nome'])

    def test_payloads_invalidos(self):
        payloads = [
            {},
            {'acordes': ['X']},
            {'acordes': []},
            {'acordes': ['X', '']},
            {'acordes': ['X', 'Y Z']},
            {'acordes': ['X', 'Y,Z']},
            {'acordes': 'X,Y'},
            {'nome': 1, 'acordes': ['X', 'Y']},
        ]
        for payload in payloads:
            with self.subTest(payload=payload):
                response = self.client.post('/sequencias', json=payload)
                self.assertEqual(response.status_code, 400)
                self.assertIn('erro', self._json(response))

    def test_duplicata_ignora_caixa_e_nome(self):
        self.client.post('/sequencias', json={
            'nome': 'Primeira', 'acordes': ['X', 'Y']
        })
        response = self.client.post('/sequencias', json={
            'nome': 'Outro nome', 'acordes': ['x', 'y']
        })
        self.assertEqual(response.status_code, 409)

    def test_duplicata_de_original(self):
        response = self.client.post('/sequencias', json={
            'acordes': ['bm', 'g', 'd', 'a']
        })
        self.assertEqual(response.status_code, 409)

    def test_busca_sequencia_original(self):
        response = self.client.get('/similares?sequencia=Bm,G,D,A&pagina=1')
        self.assertEqual(response.status_code, 200)
        musicas = self._json(response)
        self.assertEqual(len(musicas), main.TAM_PAGINA)
        self.assertIn('id_unico_musica', musicas[0])

    def test_busca_ignora_caixa(self):
        resposta_normal = self._json(
            self.client.get('/similares?sequencia=Bm,G,D,A&pagina=1'))
        resposta_minuscula = self._json(
            self.client.get('/similares?sequencia=bm,g,d,a&pagina=1'))
        self.assertEqual({m['id_unico_musica'] for m in resposta_normal},
                         {m['id_unico_musica'] for m in resposta_minuscula})

    def test_forma_concatenada_deixa_de_funcionar(self):
        response = self.client.get('/similares?sequencia=BmGDA')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._json(response), [])

    def test_sequencia_desconhecida_retorna_lista_vazia(self):
        response = self.client.get('/similares?sequencia=X,Y')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._json(response), [])

    def test_busca_sequencia_nova_sem_musicas(self):
        self.client.post('/sequencias', json={'acordes': ['X', 'Y']})
        response = self.client.get('/similares?sequencia=x,y')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._json(response), [])

    def test_busca_sequencia_nova_encontra_musica(self):
        self.client.post('/sequencias', json={'acordes': ['Bm', 'E']})
        response = self.client.get('/similares?sequencia=Bm,E')
        self.assertEqual(response.status_code, 200)
        ids = {m['id_unico_musica'] for m in self._json(response)}
        self.assertIn('the-strokes_reptilia', ids)


if __name__ == '__main__':
    unittest.main()
