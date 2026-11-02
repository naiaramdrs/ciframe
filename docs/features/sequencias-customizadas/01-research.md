# Pesquisa — Sequências de Acordes Customizadas

## Perguntas que você precisa responder

1. **Algoritmo de matching**: hoje, as 6 sequências hardcoded em `main.py` (linhas
   40-45) são comparadas contra músicas via uma tag pré-computada
   (`SEQ_FAMOSA`/`seqs_famosas`, vinda do CSV). Sequências cadastradas pelo usuário
   não têm essa tag — o matching precisa ser calculado em tempo real a partir da
   lista de acordes de cada música (`musica.acordes`/`musica.cifra`). O que vai
   definir "a sequência X aparece na música Y"? A ordem dos acordes importa?
   Repetições de acorde dentro da música importam? É preciso normalizar (ex.:
   maiúsculas/minúsculas, variações de escrita do mesmo acorde)?
2. **Validação da hipótese**: rode o algoritmo que você está considerando contra os
   dados reais em `data/top/dataset_final.csv`, para as 6 sequências hoje
   hardcoded, e confirme (ou refute) que ele reproduz os mesmos matches que o
   código atual produz via `seqs_famosas`. Esse é o bar mínimo de correção que
   você vai usar na fase de testes.
3. **Banco de dados**: quais bancos embarcados (sem serviço externo adicional) são
   viáveis dentro do container Docker único e local-only já documentado em
   `docs/adr/0001-local-only-docker-deploy.md`? O que cada opção implica para o
   `Dockerfile` atual e para a persistência dos dados entre reinícios do
   container?
4. **Frontend existente**: o que a página `#/porsequencia`
   (`static/templates/sequencia.html` +
   `static/assets/js/controllers/sequencia.js`) já faz? Repare que ela tem hoje uma
   lista *hardcoded no JavaScript* de 4 sequências (`sequencia1`..`sequencia4`),
   diferente das 6 que existem no backend — um detalhe real e pré-existente do
   código, não um erro seu, que vale entender antes de decidir o que precisa
   mudar.

## Registro das descobertas

### 1. Algoritmo de matching

**Hipótese investigada.** Uma sequência X aparece na música Y quando X ocorre
como um bloco **contíguo** de acordes dentro da cifra de Y, na mesma ordem e
preservando as repetições internas desse bloco, após normalização de caixa. Para
reproduzir a tag atual, há ainda uma condição de vocabulário: todos os acordes de Y
precisam pertencer ao conjunto de acordes de X; qualquer acorde extra fora desse
conjunto invalida o match. Portanto: **ordem importa; repetições dentro do bloco
importam; repetições fora do bloco não invalidam**, desde que o acorde pertença à
sequência; a única normalização existente é **caixa (minúsculas)**, sem
equivalência entre `C#`/`Db` ou `Am`/`Am7`.

Hoje não existe matching em tempo real para sequências. `GET /similares?sequencia=`
remove as vírgulas, procura a string exata no dicionário `sequencias`
(`main.py:40-45`) e só então verifica `str(id_seq) in musica.seqs_famosas`
(`main.py:190-197,203-223`). Sequência desconhecida retorna `[]`. O caminho
`?acordes=` é diferente: usa interseção de conjuntos e não exige sequência nem
ordem (`main.py:230-263`).

A tag `SEQ_FAMOSA` foi pré-computada por `get_famosas`
(`scripts/generate_data_set.py:7-24`) exatamente com essas duas condições:

- a sequência em minúsculas precisa ser substring literal **contígua** da cifra
  também em minúsculas (`scripts/generate_data_set.py:12-13`);
- **todos** os acordes da música precisam pertencer ao conjunto de acordes da
  sequência (`scripts/generate_data_set.py:16-20`).

Na prática, isso torna o match restritivo: a ordem e a adjacência importam,
repetições internas precisam aparecer no bloco e acordes extras desqualificam. A
geração ignora caixa, mas o endpoint não aplica essa normalização: a busca no
dicionário é case-sensitive. `musica.cifra`
preserva ordem e repetição, enquanto `musica.acordes = list(set(cifra))` perde
ambas (`musica.py:16-17`). Os scripts `normalize_chords.R` e
`simplify_chords.R` normalizam acordes, mas não são usados pelo app.

### 2. Validação da hipótese

Uma réplica literal de `get_famosas` foi rodada contra as 67.585 linhas carregadas
(o arquivo tem 67.586 linhas; `main.py:50` descarta a primeira linha de dados, que
não é cabeçalho):

- coincidências com a coluna `SEQ_FAMOSA`: **67.585 de 67.585** (0 divergências);
- músicas por tag: **199 / 296 / 4 / 5 / 7 / 3** para os ids 0 a 5 (514 no total).

Definições mais simples geraram superconjuntos e **não** reproduziram as tags:

| definição | id 0 | id 1 | id 2 | id 3 | id 4 | id 5 |
|---|---:|---:|---:|---:|---:|---:|
| tag atual | 199 | 296 | 4 | 5 | 7 | 3 |
| réplica literal | 199 | 296 | 4 | 5 | 7 | 3 |
| conjunto, sem ordem | 5.768 | 6.894 | 14.160 | 582 | 3.847 | 365 |
| contíguo | 866 | 1.216 | 3.110 | 96 | 1.039 | 132 |
| subsequência ordenada | 4.763 | 5.887 | 13.643 | 427 | 3.641 | 280 |
| só substring | 972 | 1.246 | 3.704 | 96 | 1.522 | 144 |
| só vocabulário | 873 | 958 | 24 | 53 | 18 | 57 |

Os baselines `baseline/seq1.json` e `seq2.json` têm 100 itens (primeira página de
199 e 296); `seq3.json` a `seq6.json` têm 4, 5, 7 e 3 itens. Chamadas reais ao app
confirmaram `Content-Type: text/html`, paginação e retorno vazio para sequência
desconhecida ou com caixa diferente. A ordem da primeira página varia entre
processos porque `generos` vem de um `set` (`main.py:38,92,266-272`); os conjuntos
de matches por sequência não variam.

### 3. Banco de dados

Hoje não há banco: o CSV é carregado em memória (`main.py:49-98`), as dependências
são apenas Flask e gunicorn (`requirements.txt:4-5`) e o `Dockerfile` não declara
`VOLUME` (`Dockerfile:1-12`). Os comandos documentados não usam `-v`
(`README.md:15-18`, `AGENTS.md:22-25`), e a ADR 0001 fixa um container único
local-only (`docs/adr/0001-local-only-docker-deploy.md:9-16`); a ADR 0002 ainda é
um template (`docs/adr/0002-persist-custom-sequences.md:1-8`).

Testes em Docker mostraram que um arquivo comum e um banco SQLite criados em
runtime sobrevivem a `docker stop`/`docker start` do mesmo container, mas não
existem em um novo container. O `COPY . .` é feito no build (`Dockerfile:8`) e o
que é criado em runtime fica na camada gravável; sem volume nomeado ou bind mount,
`docker rm`/novo `docker run` perdem os dados.

Opções embarcadas identificadas:

- **SQLite** (`sqlite3`): biblioteca padrão, arquivo único, disponível no
  `python:3.9-slim` (testado: SQLite 3.46.1);
- **TinyDB**: dependência pip, arquivo JSON;
- **`dbm`/`shelve`**: biblioteca padrão, arquivos chave-valor;
- **DuckDB** e **LMDB**: dependências pip, armazenamento em arquivo.

Todas são baseadas em arquivo e seguem as mesmas regras de volume acima. PostgreSQL
e MySQL exigiriam serviço/container externo, o que não corresponde ao container
único descrito na ADR 0001. O `CMD` atual roda gunicorn sem `--workers`
(`Dockerfile:12`).

### 4. Frontend existente

A rota `#/porsequencia` carrega `templates/sequencia.html` com
`SequenciaController` (`static/assets/js/routes.js:17-21`). O controller define
**quatro** sequências hardcoded (`static/assets/js/controllers/sequencia.js:2-37`):

| frontend | acordes | id no backend |
|---|---|---:|
| `sequencia1` | Bm, G, D, A | 0 |
| `sequencia2` | C, G, Am, F | 1 |
| `sequencia3` | Gm, F | 4 |
| `sequencia4` | C, C7, F, Fm | 5 |

Faltam no frontend `Em, G` (id 2) e `C, A7, Dm, G7` (id 3). Ao clicar em uma
sequência, `pesquisarPorSequencia` monta `similares?sequencia=<acordes por
vírgula>`, opcionalmente com `&generos=`, e faz um `$http.get` relativo
(`sequencia.js:63-89`). Não há formulário, `POST` nem chamada a um catálogo de
sequências.

O template lista as sequências à esquerda e mostra os resultados à direita
(`static/templates/sequencia.html:5-59`). O `select` de gênero usa a constante
hardcoded `GENEROS` (51 gêneros) de `app.js:6-58`, não o endpoint `/generos`
(`main.py:158-160`). A constante `RESTAPI` (`app.js:3-5`) não é usada por esse
controller. Os resultados são ordenados no cliente por popularidade
(`sequencia.html:42`), mas o template referencia `music.diferenca.length`
(`sequencia.html:43`), campo que o endpoint de sequência não retorna
(`main.py:210-220`).

## Trade-offs identificados

- **Matching**: o predicado atual (substring contígua + vocabulário da música
  contido no da sequência) reproduz as tags, mas é restritivo (514 matches no
  total). Conjunto, contiguidade e subsequência produzem superconjuntos; ordem,
  repetição e acordes extras alteram materialmente o resultado.
- **Banco**: opções em arquivo (SQLite, TinyDB, `dbm`/`shelve`, DuckDB, LMDB)
  cabem no container único, mas dependem de volume/bind mount para sobreviver à
  recriação do container; opções cliente-servidor exigem um segundo serviço;
  manter tudo em memória perde os dados em qualquer reinício.
- **Frontend**: a lista hardcoded de 4 sequências não consulta o backend, omite os
  ids 2 e 3 e só suporta busca por `GET`; qualquer catálogo dinâmico ou cadastro
  não existe hoje. A lista de gêneros também é duplicada no JavaScript em vez de
  vir de `/generos`.
