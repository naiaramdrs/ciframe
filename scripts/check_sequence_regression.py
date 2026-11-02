#!/usr/bin/env python3
import json
import os
import sys
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
_TEMP_DB = None

if 'SEQUENCES_DB' not in os.environ:
    _TEMP_DB = tempfile.TemporaryDirectory()
    os.environ['SEQUENCES_DB'] = str(Path(_TEMP_DB.name) / 'regression.db')

os.chdir(BASE_DIR)
sys.path.insert(0, str(BASE_DIR))

import main  # noqa: E402
from sequencias_db import ler_sequencias_originais  # noqa: E402


def ids_musicas(musicas):
    return {musica.id_unico_musica for musica in musicas}


def ids_json(musicas):
    return {musica['id_unico_musica'] for musica in musicas}


def carregar_baseline(id_seq):
    caminho = BASE_DIR / 'baseline' / ('seq%d.json' % (id_seq + 1))
    with caminho.open(encoding='utf-8') as arquivo:
        return ids_json(json.load(arquivo))


def buscar_similares(cliente, acordes):
    encontrados = []
    pagina = 1
    while True:
        response = cliente.get('/similares', query_string={
            'sequencia': ','.join(acordes),
            'pagina': pagina,
        })
        if response.status_code != 200:
            raise RuntimeError('GET /similares retornou %d na página %d' % (
                response.status_code, pagina))
        lote = json.loads(response.get_data(as_text=True))
        encontrados.extend(lote)
        if len(lote) < main.TAM_PAGINA:
            return encontrados
        pagina += 1


def comparar_sequencia(id_seq, nome, acordes):
    esperado = [musica for musica in main.musicas.values()
                if str(id_seq) in musica.seqs_famosas]
    encontrado = buscar_similares(main.app.test_client(), acordes)

    falhas = []
    if len(esperado) != len(encontrado):
        falhas.append('count %d != %d' % (len(esperado), len(encontrado)))

    ids_esperados = ids_musicas(esperado)
    ids_encontrados = ids_json(encontrado)
    if ids_esperados != ids_encontrados:
        falhas.append('ids divergentes: faltando=%s extras=%s' % (
            sorted(ids_esperados - ids_encontrados),
            sorted(ids_encontrados - ids_esperados)))
    if len(ids_encontrados) != len(encontrado):
        falhas.append('ids repetidos entre páginas')

    ids_baseline = carregar_baseline(id_seq)
    ids_primeira_pagina = ids_json(encontrado[:main.TAM_PAGINA])
    if id_seq < 2:
        if not ids_baseline <= ids_encontrados:
            falhas.append('baseline histórico fora do conjunto completo: %s' % (
                sorted(ids_baseline - ids_encontrados)))
    elif ids_primeira_pagina != ids_baseline:
        falhas.append('baseline divergente: faltando=%s extras=%s' % (
            sorted(ids_baseline - ids_primeira_pagina),
            sorted(ids_primeira_pagina - ids_baseline)))

    print('seq%d (%s): esperado=%d encontrado=%d baseline=%d' % (
        id_seq, nome, len(esperado), len(encontrado), len(ids_baseline)))
    if falhas:
        for falha in falhas:
            print('  FALHA: %s' % falha)
        return False
    return True


def main_check():
    ok = True
    for id_seq, nome, acordes in ler_sequencias_originais():
        ok = comparar_sequencia(id_seq, nome, acordes) and ok
    print('OK' if ok else 'REGRESSÃO DETECTADA')
    return 0 if ok else 1


if __name__ == '__main__':
    codigo = main_check()
    if _TEMP_DB is not None:
        _TEMP_DB.cleanup()
    sys.exit(codigo)
