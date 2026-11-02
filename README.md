# deciframe

Descubra as músicas que você já sabe tocar (e ainda não faz ideia). Busque por
título/artista, gênero, pelos acordes que você já manja, ou por sequências de
acordes famosas — o deciframe cruza isso com uma base de cifras e sugere
músicas parecidas.

Stack: backend Flask (Python) servindo uma API JSON + um frontend AngularJS
estático. As músicas e gêneros vêm de um CSV em memória; as sequências de acordes
customizadas ficam em SQLite.

## Rodando localmente

### Com Docker

```
docker build -t ciframe .
docker run -p 8080:8080 -v deciframe-data:/data ciframe
```

O volume `deciframe-data` preserva o catálogo de sequências em
`/data/deciframe.db` entre reinícios e recriações do container.

Acesse [http://localhost:8080](http://localhost:8080).

### Com virtualenv

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Por padrão, o banco local fica em `instance/deciframe.db`. Para usar outro
caminho, defina `SEQUENCES_DB` (por exemplo,
`SEQUENCES_DB=/tmp/deciframe.db python main.py`).

Acesse [http://localhost:5000](http://localhost:5000).

---

Para convenções de contribuição, veja [CONTRIB.md](CONTRIB.md). Licença: [LICENSE](LICENSE).
