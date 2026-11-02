# Proposta — Sequências de Acordes Customizadas

## Abordagem escolhida

A abordagem escolhida é a **Proposta 1**: SQLite para o catálogo e uma única regra
de matching, aplicada igualmente às sequências originais e às novas.

### Algoritmo de matching

A regra é única para todas as sequências, antigas e novas. Seja `S` a lista
ordenada de acordes cadastrada e `C` a lista `musica.cifra`; ambas são comparadas
token a token, ignorando caixa. `S` aparece em `C` quando ocorre como uma fatia
**contígua** de `C`, na mesma ordem e preservando as repetições internas, e quando
**todos** os tokens de `C` pertencem ao conjunto de tokens de `S`. Um acorde extra
em `C` invalida o match.

Essa é a mesma semântica da tag `SEQ_FAMOSA`
(`scripts/generate_data_set.py:7-24`), agora calculada em tempo real sobre
`musica.cifra`; `musica.acordes` não é usado porque
`list(set(cifra))` perde ordem e repetição (`musica.py:16-17`). Não há
normalização enarmônica nem de sufixos: `C#` e `Db`, ou `Am` e `Am7`, continuam
distintos.

`SEQ_FAMOSA` deixa de ser consultada no fluxo de busca e permanece no CSV apenas
como referência para os testes de regressão. A validação mínima é reproduzir, para
as 6 sequências originais, os mesmos conjuntos de ids e os counts já medidos
(199/296/4/5/7/3; 67.585/67.585 linhas sem divergência).

**Limitação aceita:** como a música não pode ter acordes fora da sequência,
sequências novas podem retornar poucas músicas ou nenhuma. Isso é consequência
direta de manter a mesma regra das 6 originais, não um defeito a corrigir nesta
feature.

### Banco de dados

SQLite, via `sqlite3` da biblioteca padrão. Ele cabe no container único, não exige
serviço externo, suporta a restrição de unicidade necessária para duplicatas e já
está disponível no `python:3.9-slim` (SQLite 3.46.1). O catálogo de músicas e
gêneros continua vindo do CSV em memória (`main.py:49-98`); apenas o catálogo de
sequências vai para o banco.

O arquivo fica em `/data/deciframe.db`, configurável por `SEQUENCES_DB`. O
`Dockerfile` passa a declarar `VOLUME /data`, e os comandos de execução passam a
usar um volume nomeado, por exemplo `-v deciframe-data:/data`, para que o catálogo
sobreviva à recriação do container.

### Esquema de dados (alto nível)

Uma tabela `sequencias`:

- `id`: chave primária; as 6 originais são semeadas com ids 0–5;
- `nome`: texto opcional, podendo ser `NULL`;
- `acordes`: lista ordenada em JSON, preservando repetições;
- `acordes_norm`: forma canônica em minúsculas da lista, com restrição `UNIQUE`;
- `criado_em`: timestamp de criação.

O seed é idempotente e usa os acordes de `main.py:40-45` e os nomes de
`data/mapeamento_sequencias_famosas.txt:1-6`.

### API

- `GET /sequencias`: retorna a lista do catálogo, com `id`, `nome`, `acordes` e
  `criado_em`.
- `POST /sequencias`: recebe `{"nome": "...", "acordes": ["Bm", "G", "D", "A"]}`.
  `nome` é opcional; quando ausente ou vazio, fica `NULL` e o frontend exibe os
  próprios acordes. `acordes` precisa ter pelo menos 2 itens; cada item deve ser
  uma string não vazia e sem whitespace. Caso contrário, retorna `400`.
- A chave de duplicata é `acordes_norm`, sem considerar o nome. Uma sequência já
  existente, ignorando caixa, retorna `409`.
- Acordes fora do dataset são aceitos: não há validação contra o conjunto global
  `acordes`; eles simplesmente podem não encontrar músicas.
- `GET /similares?sequencia=...` mantém o formato atual: recebe acordes separados
  por vírgula, procura a sequência pela chave canônica, aplica o matching em tempo
  real e preserva `generos`, `pagina` e o retorno `[]` para sequência desconhecida
  (`main.py:170-201`).
- Todos os endpoints continuam retornando `json.dumps(...)`, inclusive os novos.

### Frontend

`SequenciaController` deixa de definir as 4 sequências fixas de
`static/assets/js/controllers/sequencia.js:2-37` e passa a carregar
`GET /sequencias` na inicialização. A resposta é convertida para o formato que o
template já usa (`{acorde, cor}`), de modo que `sequencia.html:6-7` renderize as 6
originais e as novas.

A página ganha um formulário com nome opcional e acordes separados por vírgula. O
controller divide e remove espaços ao redor dos separadores, valida no cliente o
mínimo de 2 acordes e envia `POST /sequencias`; o servidor continua sendo a
autoridade da validação. Em `201`, o catálogo é recarregado; `400` e `409` são
exibidos ao usuário. A busca continua usando `pesquisarPorSequencia` e
`GET /similares` (`sequencia.js:55-89`), então sequências antigas e novas seguem o
mesmo fluxo.

## Alternativas consideradas e descartadas

- **Proposta 2 — dois modos de matching (`legacy` para as 6 e `contiguous` para as
  novas):** descartada porque cria duas semânticas no mesmo catálogo, dificulta
  explicar e testar o comportamento e contraria a decisão de usar a mesma regra
  para todas as sequências. A limitação de recall das novas é aceita.
- **TinyDB:** descartada por adicionar dependência externa, reescrever o arquivo
  JSON inteiro e oferecer menos garantias de concorrência e de restrição de
  unicidade do que SQLite. O volume de dados é pequeno, mas o catálogo é aberto e
  anônimo, e a unicidade de duplicatas precisa ser garantida no banco.
- **`shelve`/`dbm`:** descartados por serem armazenamentos chave-valor sem schema,
  sem restrição `UNIQUE` e com semântica de concorrência inadequada para um
  catálogo consultável e gravável. SQLite resolve esses pontos sem dependência
  extra.

## Escopo explícito

**Dentro do escopo:**

- criar a tabela e semear as 6 sequências originais com ids 0–5;
- cadastrar sequências anônimas via `POST /sequencias`;
- listar o catálogo via `GET /sequencias`;
- calcular o matching em tempo real para qualquer sequência do catálogo;
- manter os resultados das 6 originais iguais aos atuais;
- persistir o catálogo em SQLite com volume Docker;
- atualizar `#/porsequencia` para carregar o catálogo real e permitir cadastro;
- validar regressão, duplicatas, payload inválido e persistência entre reinícios.

**Fora do escopo (e por quê):**

- migrar músicas ou gêneros para o banco: o CSV em memória continua sendo a fonte
  fixa do enunciado;
- login, moderação, rate limiting ou edição/exclusão de sequências: o catálogo é
  aberto e anônimo, e o enunciado não pede essas operações;
- normalização enarmônica, de sufixos ou de grafias alternativas: a regra escolhida
  mantém apenas a comparação ignorando caixa;
- trocar `json.dumps` por `jsonify` ou alterar o formato de resposta de
  `/similares`;
- dinamizar a lista de gêneros do frontend: ela continua como está nesta feature;
- otimizações de índice/cache ou suporte a múltiplos workers: o `CMD` atual usa
  gunicorn sem `--workers` e a escala é local.
