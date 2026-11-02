import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

ARQUIVO_MAPEAMENTO = Path(__file__).resolve().parent / 'data' / 'mapeamento_sequencias_famosas.txt'
BANCO_LOCAL_PADRAO = Path(__file__).resolve().parent / 'instance' / 'deciframe.db'


class SequenciaDuplicada(Exception):
    pass


def resolver_caminho_banco(caminho=None):
    if caminho:
        return Path(caminho)
    return Path(os.environ.get('SEQUENCES_DB') or BANCO_LOCAL_PADRAO)


def conectar(caminho=None):
    caminho = resolver_caminho_banco(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(caminho), timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA busy_timeout = 5000')
    return conn


def serializar_acordes(acordes):
    return json.dumps(acordes, ensure_ascii=False, separators=(',', ':'))


def chave_canonica_acordes(acordes):
    return serializar_acordes([acorde.lower() for acorde in acordes])


def _agora():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def ler_sequencias_originais():
    sequencias = []
    with ARQUIVO_MAPEAMENTO.open(encoding='utf-8') as arquivo:
        for linha in arquivo:
            linha = linha.rstrip('\n')
            if not linha.strip():
                continue
            id_seq, nome, acordes_texto = linha.split(',', 2)
            acordes = [acorde.strip() for acorde in acordes_texto.split(' - ')]
            sequencias.append((int(id_seq), nome.strip(), acordes))
    return sequencias


def _linha_para_dict(linha):
    return {
        'id': linha['id'],
        'nome': linha['nome'],
        'acordes': json.loads(linha['acordes']),
        'criado_em': linha['criado_em'],
    }


def inicializar_banco(caminho=None):
    with closing(conectar(caminho)) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sequencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                acordes TEXT NOT NULL,
                acordes_norm TEXT NOT NULL UNIQUE,
                criado_em TEXT NOT NULL
            )
        ''')
        for id_seq, nome, acordes in ler_sequencias_originais():
            conn.execute('''
                INSERT OR IGNORE INTO sequencias
                    (id, nome, acordes, acordes_norm, criado_em)
                VALUES (?, ?, ?, ?, ?)
            ''', (id_seq, nome, serializar_acordes(acordes),
                  chave_canonica_acordes(acordes), _agora()))
        conn.commit()


def listar_sequencias(caminho=None):
    with closing(conectar(caminho)) as conn:
        linhas = conn.execute('''
            SELECT id, nome, acordes, criado_em
            FROM sequencias
            ORDER BY id
        ''').fetchall()
    return [_linha_para_dict(linha) for linha in linhas]


def buscar_sequencia_por_acordes(acordes, caminho=None):
    if not acordes:
        return None

    with closing(conectar(caminho)) as conn:
        linha = conn.execute('''
            SELECT id, nome, acordes, criado_em
            FROM sequencias
            WHERE acordes_norm = ?
        ''', (chave_canonica_acordes(acordes),)).fetchone()

    if linha is None:
        return None
    return _linha_para_dict(linha)


def criar_sequencia(nome, acordes, caminho=None):
    nome = nome.strip() if nome else None
    if not nome:
        nome = None
    criado_em = _agora()

    with closing(conectar(caminho)) as conn:
        try:
            cursor = conn.execute('''
                INSERT INTO sequencias (nome, acordes, acordes_norm, criado_em)
                VALUES (?, ?, ?, ?)
            ''', (nome, serializar_acordes(acordes),
                  chave_canonica_acordes(acordes), criado_em))
            conn.commit()
        except sqlite3.IntegrityError as erro:
            if 'UNIQUE' in str(erro).upper():
                raise SequenciaDuplicada()
            raise

        return {
            'id': cursor.lastrowid,
            'nome': nome,
            'acordes': acordes,
            'criado_em': criado_em,
        }
