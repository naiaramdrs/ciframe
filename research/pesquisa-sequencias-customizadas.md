# Pesquisa — Sequências de Acordes Customizadas (estado atual)

## Resumo

O deciframe não possui banco de dados: `main.py` carrega `data/top/dataset_final.csv`
em memória na inicialização e cria objetos `Musica`; a coluna `SEQ_FAMOSA` desse CSV
já traz uma tag pré-computada que o endpoint `GET /similares?sequencia=...` usa para
encontrar músicas. A tag não é um matching genérico de sequência: ela é gerada por
`scripts/generate_data_set.py` com duas condições simultâneas — a sequência precisa
aparecer como substring literal contígua da cifra em minúsculas **e** todos os
acordes da música precisam pertencer ao conjunto de acordes da sequência. Uma
réplica literal desse predicado reproduziu 100% das tags atuais (67.585 de 67.585
linhas carregadas), enquanto definições mais simples (conjunto, subsequência,
contiguidade) produziram superconjuntos. No Docker atual não há volume declarado; arquivos criados
em tempo de execução sobrevivem a `stop`/`start` do mesmo container, mas não à
remoção/criação de um novo container. No frontend, `#/porsequencia` tem quatro
sequências hardcoded em JavaScript e só faz `GET /similares`; não há formulário de
cadastro nem leitura de catálogo do backend.

## Evidências e método

- Leitura integral de `docs/features/sequencias-customizadas/01-research.md` e dos
  demais arquivos da feature (`00-enunciado.md`, `02-proposal.md`, `03-plan.md`,
  `04-test-report.md`).
- Leitura integral de `main.py`, `musica.py`, `Dockerfile`, `requirements.txt`,
  `README.md`, `AGENTS.md`, ADRs e dos arquivos de frontend/scripts citados abaixo.
- Recarga do CSV com a mesma lógica de `main.py:49-98` e comparação com as tags da
  coluna `SEQ_FAMOSA`: 67.585 linhas carregadas; 514 linhas com alguma tag não vazia.
  O arquivo tem 67.586 linhas de dados e nenhum cabeçalho; `main.py:50` descarta a
  primeira linha com `f.readline()`, de modo que o app carrega 67.585 músicas (a
  primeira linha é `14-bis,a-qualquer-tempo,...`, com tag `NA`).
- Réplica de `get_famosas` (`scripts/generate_data_set.py:7-24`) executada contra as
  67.585 linhas: 67.585 coincidências com a coluna do CSV (0 divergências).
- Chamadas reais via `Flask.test_client()` dentro da imagem `ciframe:latest`
  (Python 3.9.25, Flask 3.1.3), incluindo sequência conhecida, sequência desconhecida,
  variação de caixa/ordem e paginação.
- Testes de persistência em Docker com arquivo comum e com SQLite: criação em um
  container, `docker stop`/`docker start` e criação de um novo container.
- Comparação com os arquivos presentes em `baseline/seq1.json` … `baseline/seq6.json`.

## 1. Algoritmo de matching hoje

### 1.1 Onde o matching acontece

O backend não calcula se uma sequência aparece em uma música no momento da busca.
As sequências famosas usadas pela API vêm de duas peças fixas:

1. O dicionário `sequencias` em `main.py:40-45`, que mapeia a string concatenada de
   acordes para um id inteiro:

   ```python
   sequencias = {'BmGDA' : 0,
           'CGAmF' : 1,
           'EmG' : 2,
           'CA7DmG7' : 3,
           'GmF' : 4,
           'CC7FFm' : 5}
   ```

2. A coluna `SEQ_FAMOSA` (índice 7 do CSV, `main.py:33`), carregada em
   `main.py:63` e guardada em `musica.seqs_famosas` (`musica.py:18`).

O endpoint `GET /similares` trata `sequencia` assim:

- remove as vírgulas do parâmetro (`main.py:191`);
- faz uma busca exata no dicionário `sequencias` (`main.py:194`);
- se a string existir, obtém o id e chama
  `get_similares_por_sequencia(id_seq, generos_key)` (`main.py:195-196`);
- se a string não existir, retorna uma lista vazia (`main.py:192,197`).

`get_similares_por_sequencia` percorre as músicas filtradas por gênero e inclui
aquelas em que `str(id_seq) in musica.seqs_famosas` (`main.py:203-223`). Não há
comparação contra `musica.cifra` nem contra `musica.acordes` nesse caminho.

O outro caminho de `/similares` — `?acordes=...` ou `?id_unico_musica=...` — usa
interseção de conjuntos de acordes (`main.py:230-263`): uma música entra se tiver
pelo menos um acorde em comum. Esse caminho ignora ordem, repetição e tamanho da
sequência; ele não é um matching de sequência.

### 1.2 Predicado que gera a tag `SEQ_FAMOSA`

A tag foi pré-computada por `get_famosas`, em `scripts/generate_data_set.py:7-24`.
Para cada uma das seis sequências:

- a cifra da música e a sequência são convertidas para minúsculas
  (`scripts/generate_data_set.py:12`);
- a sequência precisa ocorrer como substring literal da cifra em minúsculas
  (`scripts/generate_data_set.py:13`);
- depois, **todos** os acordes da música precisam estar na lista de acordes da
  sequência (`scripts/generate_data_set.py:16-20`).

Em pseudocódigo, o predicado efetivo é:

```text
sequencia_minuscula in cifra_minuscula
E
todos os acordes da cifra pertencem ao conjunto de acordes da sequencia
```

A segunda condição é reforçada pelo código porque o laço percorre a cifra inteira
(`for l in acorde.split(';')`) e falha se qualquer acorde da música não estiver em
`tokens = s.split(';')` (`scripts/generate_data_set.py:16-20`).

Consequências observáveis desse predicado:

- **Ordem e adjacência importam.** A primeira condição é uma busca de substring na
  string com `;`. Por isso a sequência precisa aparecer contígua e na ordem
  cadastrada. Por exemplo, `30-seconds-to-mars,city-of-angels` contém
  `D;A;Bm;G;D;A;...` e recebe a tag `0` (`data/top/dataset_final.csv:136`).
- **Acordes extras na música desqualificam.** `3-doors-down,every-time-you-go`
  contém `Bm;G;D;A` em `...G;D;Bm;G;D;A...` (`data/top/dataset_final.csv:78`), mas
  não recebe a tag `0` porque a música tem outros acordes (`G6`, `D9`, `B9`, `C`,
  `A`, `A6` etc.) fora do conjunto `{Bm, G, D, A}`.
- **Repetições:** uma repetição entre os acordes da ocorrência quebra a substring
  contígua; repetições em outras partes da música não quebram a segunda condição,
  porque ela compara tokens contra o conjunto de tokens da sequência, sem contar
  ocorrências. A cifra bruta preserva repetições; `musica.acordes` não as preserva.
- **Caixa:** a geração da tag compara tudo em minúsculas
  (`scripts/generate_data_set.py:12`). Já a busca da API no dicionário `sequencias`
  é exata e sensível à caixa (`main.py:194`): `BmGDA` funciona, `bmgda` não.
- **Variações de escrita:** não há normalização de acordes no runtime. A comparação
  é por token literal após `lower()`; `C#` e `Db` são tokens diferentes, assim como
  `Am` e `Am7`, e acordes com baixo invertido como `E/B` são tokens próprios. A
  função `limpa_cifra` apenas remove vazios, trata tablaturas com `|` e separa por
  espaço (`main.py:11-23`); ela não muda caixa nem simplifica acordes.
- **Normalização offline não usada:** `scripts/normalize_chords.R` e
  `scripts/simplify_chords.R` convertem acordes para graus (`I`, `II`, …) usando
  `data/transposition_matrix2.csv` (`scripts/normalize_chords.R:3-36`,
  `scripts/simplify_chords.R:3-34`), mas `main.py` não importa nem executa esses
  scripts; a única leitura de dados do app é `data/top/dataset_final.csv`
  (`main.py:49`).

### 1.3 Dados disponíveis para uma checagem em tempo real

Embora não sejam usados no endpoint de sequência, os objetos `Musica` guardam:

- `self.cifra = cifra`, lista na ordem em que os acordes aparecem e com repetições
  (`musica.py:16`; preenchida em `main.py:58-61`);
- `self.acordes = list(set(cifra))`, lista sem ordem e sem repetições
  (`musica.py:17`).

Não existe hoje nenhum caminho de código que aplique uma sequência cadastrada pelo
usuário a `musica.cifra` ou `musica.acordes`.

## 2. Validação contra os dados reais

### 2.1 Réplica do predicado atual

Foi implementada uma réplica literal de `get_famosas` sobre a coluna `CIFRA` e
comparada com a coluna `SEQ_FAMOSA` de `data/top/dataset_final.csv`:

- linhas carregadas: **67.585**;
- linhas com tag não vazia: **514**;
- linhas em que a réplica e a tag do CSV coincidem: **67.585**;
- divergências: **0**.

Distribuição das tags atuais:

| id | sequência | músicas com a tag |
|---:|---|---:|
| 0 | Bm, G, D, A | 199 |
| 1 | C, G, Am, F | 296 |
| 2 | Em, G | 4 |
| 3 | C, A7, Dm, G7 | 5 |
| 4 | Gm, F | 7 |
| 5 | C, C7, F, Fm | 3 |

O CSV atual só contém valores de tag simples (`0` a `5`) ou vazio; nenhuma música
tem mais de um id. O gerador, porém, chama `get_famosas` e junta os ids retornados
sem separador com `''.join(...)` (`scripts/generate_data_set.py:86-88`), o que
produziria algo como `01` para uma música que casasse com duas sequências. A
checagem da API é por igualdade de item na lista
(`str(id_seq) in musica.seqs_famosas`, `main.py:209`), então `0` e `1` não casariam
com `01`.

### 2.2 Definições alternativas testadas

As definições abaixo foram aplicadas ao mesmo CSV, usando `musica.cifra` já limpa
por `limpa_cifra` e comparação em minúsculas:

| id | tag atual | réplica literal | conjunto (sem ordem) | contíguo | subsequência ordenada | só substring | só vocabulário |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 199 | 199 | 5.768 | 866 | 4.763 | 972 | 873 |
| 1 | 296 | 296 | 6.894 | 1.216 | 5.887 | 1.246 | 958 |
| 2 | 4 | 4 | 14.160 | 3.110 | 13.643 | 3.704 | 24 |
| 3 | 5 | 5 | 582 | 96 | 427 | 96 | 53 |
| 4 | 7 | 7 | 3.847 | 1.039 | 3.641 | 1.522 | 18 |
| 5 | 3 | 3 | 365 | 132 | 280 | 144 | 57 |

Definições usadas na tabela:

- **conjunto:** todos os acordes da sequência estão presentes na música, sem
  considerar ordem, repetição ou acordes extras;
- **contíguo:** a sequência aparece como bloco contíguo na ordem da cifra;
- **subsequência ordenada:** os acordes aparecem na ordem da sequência, mas não
  precisam ser adjacentes;
- **só substring:** apenas a primeira condição de `get_famosas`;
- **só vocabulário:** apenas a segunda condição de `get_famosas`.

Resultado factual: a réplica literal é a única que reproduz exatamente os conjuntos
de tags. Todas as definições mais simples geraram superconjuntos; nenhuma música
com tag ficou de fora de qualquer uma delas (a condição da tag é mais restritiva).

### 2.3 Baseline e comportamento do endpoint

Os arquivos `baseline/seq1.json` … `baseline/seq6.json` contêm resultados de uma
execução anterior:

- `seq1.json` e `seq2.json`: 100 itens cada (primeira página de 199 e 296);
- `seq3.json`: 4 itens; `seq4.json`: 5; `seq5.json`: 7; `seq6.json`: 3.

Todos os ids presentes nos baselines são subconjunto das tags calculadas acima.
Para os ids 2 a 5 (em `baseline/seq3.json` a `baseline/seq6.json`), o baseline
contém exatamente o conjunto total de tags.

Chamadas ao app dentro de `ciframe:latest` confirmaram:

| requisição | resposta |
|---|---|
| `/similares?sequencia=Bm,G,D,A` | HTTP 200, `Content-Type: text/html; charset=utf-8`, lista com 100 itens |
| `/similares?sequencia=BmGDA` | mesmo resultado da forma com vírgulas |
| `/similares?sequencia=C,G,Am,F&pagina=2` | lista com 100 itens (segunda página) |
| `/similares?sequencia=Em,G` | lista com 4 itens |
| `/similares?sequencia=bmgda` e `/similares?sequencia=bm,g,d,a` | lista vazia (busca sensível à caixa) |
| `/similares?sequencia=Am,F,C,G` | lista vazia |
| `/similares?sequencia=XYZ` | lista vazia |
| `/generos` | HTTP 200, lista com 52 gêneros |

A ordem dos resultados e a composição da primeira página não são estáveis entre
processos. `generos` nasce de um `set` (`main.py:38`), é convertido para lista
(`main.py:92`) e é essa lista que `apply_filtro` percorre (`main.py:266-272`);
`genero_musicas` é ordenado por popularidade dentro de cada gênero
(`main.py:95-96`). Com `PYTHONHASHSEED=1` e `PYTHONHASHSEED=2`, a lista
`main.generos[:5]` e os primeiros resultados de `Bm,G,D,A` mudaram. Os conjuntos
de matches por sequência, porém, permaneceram iguais aos das tags.

## 3. Banco de dados e Docker

### 3.1 Estado atual

- Não há banco de dados. `README.md:8-9` descreve “CSV em memória (sem banco)” e
  `AGENTS.md:9-11` repete que `main.py` carrega o CSV uma vez e “there is no
  database”.
- As únicas dependências declaradas são Flask e gunicorn
  (`requirements.txt:4-5`). Nenhum driver ou biblioteca de banco está listado.
- O `Dockerfile` usa `python:3.9-slim`, instala `requirements.txt`, copia o código
  com `COPY . .`, expõe `8080` e roda gunicorn
  (`Dockerfile:1-12`). Não há instrução `VOLUME`.
- `.dockerignore` exclui `.git`, `.venv`, `__pycache__` e `*.pyc`
  (`.dockerignore:1-4`); `data/` não é excluído.
- Os comandos documentados são `docker build -t ciframe .` e
  `docker run -p 8080:8080 ciframe` (`README.md:15-18`, `AGENTS.md:22-25`), sem
  `-v`/volume.
- A ADR `docs/adr/0001-local-only-docker-deploy.md:9-16` registra a decisão de um
  único `Dockerfile` local, com o backend mantido em `main.py`, busca em CSV em
  memória, sem serviço externo e sem alvo de nuvem definido.
- A ADR de persistência ainda é um template não preenchido:
  `docs/adr/0002-persist-custom-sequences.md:1-8`.

### 3.2 Persistência no Docker atual

O teste feito com a imagem `ciframe:latest` mostrou:

1. Um arquivo criado em `/app` dentro de um container existente continuou existindo
   após `docker stop` e `docker start` do mesmo container.
2. Um novo container criado a partir da mesma imagem não tinha o arquivo.
3. O mesmo comportamento ocorreu com um banco SQLite: a tabela e as linhas
   sobreviveram ao `stop`/`start` do mesmo container e não existiam em um novo
   container.

Isso decorre do modelo do Docker: o `COPY . .` grava conteúdo no momento do build
(`Dockerfile:8`), enquanto arquivos criados em runtime ficam na camada gravável do
container. Sem volume nomeado ou bind mount, `docker rm` e um novo `docker run`
partem da imagem novamente. Um volume montado sobre um diretório do app esconde o
conteúdo da imagem naquele ponto de montagem.

O `CMD` atual roda gunicorn sem `--workers` (`Dockerfile:12`). Com um único worker,
os dicionários globais de `main.py` são um único processo. Com múltiplos workers,
cada processo teria sua própria cópia desses globais; um banco em arquivo seria
compartilhado pelo sistema de arquivos, com as regras de concorrência de cada
biblioteca.

### 3.3 Opções embarcadas identificadas

A tabela abaixo registra características factuais das opções, não uma escolha.

| opção | dependência | armazenamento | presença no projeto hoje | implicação para `Dockerfile`/persistência |
|---|---|---|---|---|
| SQLite (`sqlite3`) | biblioteca padrão do Python | arquivo único | módulo disponível no `python:3.9-slim` (testado: SQLite 3.46.1) | mesmo modelo de arquivo: sobrevive a `stop`/`start`, exige volume/bind mount para sobreviver a `docker rm`/novo container |
| TinyDB | pacote Python externo | arquivo JSON | não está em `requirements.txt` | exigiria adicionar dependência e instalar no build; persistência de arquivo com as mesmas regras de volume |
| `dbm`/`shelve` | biblioteca padrão do Python | um ou mais arquivos chave-valor | módulo disponível | mesmas regras de volume; sem SQL; formato dependente da implementação `dbm` |
| DuckDB | pacote Python externo | arquivo | não instalado | exigiria dependência no build; mesmas regras de volume para o arquivo |
| LMDB | pacote Python externo | arquivo/memória mapeada | não instalado | exigiria dependência no build; mesmas regras de volume |
| PostgreSQL/MySQL | serviço externo | servidor separado | não há serviço nem driver no projeto | exigiria outro container/serviço, o que não corresponde ao container único local-only descrito em `docs/adr/0001-local-only-docker-deploy.md:9-16` |
| dicionários/globais Python | nenhuma | memória do processo | é o que existe hoje (`main.py:37-98`) | não há persistência; qualquer reinício do processo perde o estado |

O arquivo `data/top/dataset_final.csv` continua sendo copiado para a imagem no
build (`Dockerfile:8`) e lido uma vez na importação (`main.py:49`); `AGENTS.md:45`
registra que editar esse CSV exige reiniciar o processo.

## 4. Frontend existente em `#/porsequencia`

### 4.1 Rota e carregamento

A rota está em `static/assets/js/routes.js:17-21`: `#/porsequencia` carrega
`templates/sequencia.html` com `SequenciaController` e `controllerAs: "Sequencia"`.
O controller é incluído no `index.html` em `static/index.html:145`; a aplicação usa
AngularJS 1.4.9 e jQuery via CDN (`static/index.html:125-134`).

### 4.2 Controller: catálogo hardcoded

`static/assets/js/controllers/sequencia.js:2-37` define quatro objetos
`sequencia1` … `sequencia4` e os empilha em `vm.sequenciasFamosas`
(`sequencia.js:33-37`). Cada acorde é um objeto `{ acorde, cor }`, com a mesma cor
`#2E1C74` para todos (`sequencia.js:5-30`). Todos os objetos têm `index: 1`
(`sequencia.js:3,11,19,25`), valor que não é lido em outro ponto do arquivo.

Correspondência entre o frontend e as seis sequências do backend:

| frontend | acordes | chave gerada | id no backend | presente no backend? |
|---|---|---|---:|---|
| `sequencia1` | Bm, G, D, A | `BmGDA` | 0 | sim |
| `sequencia2` | C, G, Am, F | `CGAmF` | 1 | sim |
| `sequencia3` | Gm, F | `GmF` | 4 | sim |
| `sequencia4` | C, C7, F, Fm | `CC7FFm` | 5 | sim |
| — | Em, G | `EmG` | 2 | **não aparece no frontend** |
| — | C, A7, Dm, G7 | `CA7DmG7` | 3 | **não aparece no frontend** |

As seis sequências do backend estão em `main.py:40-45`; os nomes legíveis estão em
`data/mapeamento_sequencias_famosas.txt:1-6`.

O restante do estado do controller (`sequencia.js:38-45`):

- `vm.minhaSequencia = {}`;
- `vm.isSearching = false`;
- `vm.showSearchResultsCount = false`;
- `vm.esfigeSpeech = ""`;
- `vm.musics = []`;
- `vm.generos = GENEROS` (constante hardcoded de `app.js`);
- `vm.meuGenero = ""`;
- `vm.progressbar = ngProgressFactory.createInstance()`.

Funções do controller:

- `vm.temAcorde(acorde)` verifica `vm.minhaSequencia.acordes.indexOf(acorde) > -1`
  (`sequencia.js:47-53`); no template ela é chamada com o objeto `acordeon`, não com
  o nome do acorde (`static/templates/sequencia.html:7`).
- `createChordsString(chords)` concatena os nomes com vírgula e remove a última
  vírgula (`sequencia.js:55-61`).
- `vm.pesquisarPorSequencia(sequencia)` recebe opcionalmente uma sequência, define
  `vm.minhaSequencia`, inicia a progressbar, limpa `vm.musics` e monta
  `similares?sequencia=<acordes separados por vírgula>`; se houver gênero
  selecionado, acrescenta `&generos=<gênero>` (`sequencia.js:63-77`).
- A URL é relativa porque `var apiUrl = ""` (`sequencia.js:72`). A constante
  `RESTAPI` existe em `static/assets/js/app.js:3-5` com
  `http://localhost:5003`, mas não é usada por este controller.
- Em sucesso, o controller preenche `vm.musics` com a resposta e muda o texto da
  esfige (`sequencia.js:78-84`); em erro, mostra “Ops! Algo errado.”
  (`sequencia.js:85-89`).
- `vm.limparPesquisa()` zera a sequência selecionada e os resultados
  (`sequencia.js:92-95`).
- `vm.goToLirics(music)` abre `music.url` em nova janela (`sequencia.js:97-99`).
- `vm.goToResults()` esconde o contador e rola até `#results`
  (`sequencia.js:101-104`).

Não há no controller formulário, campo de texto, botão de cadastro, `POST`, nem
chamada a um endpoint de catálogo de sequências.

### 4.3 Template

`static/templates/sequencia.html` tem dois painéis:

- à esquerda, um `ng-repeat` sobre `Sequencia.sequenciasFamosas`; cada sequência é
  clicável e chama `Sequencia.pesquisarPorSequencia(sequencia)`; os acordes são
  renderizados pelo componente `df-hex` (`sequencia.html:5-8`);
- à direita, o painel de resultados. Ele só aparece quando
  `Sequencia.minhaSequencia.acordes.length` é verdadeiro (`sequencia.html:19`),
  mostra o texto de busca (`sequencia.html:20`), um `select` de gênero ligado a
  `Sequencia.generos` com `ng-change` que dispara nova busca
  (`sequencia.html:24-30`) e os acordes da sequência selecionada, cujo clique chama
  `limparPesquisa()` (`sequencia.html:34`).

Os resultados são renderizados em `ng-repeat="music in Sequencia.musics |
orderBy:'-popularidade'"` (`sequencia.html:42`), com `ng-hide` baseado em
`music.diferenca.length` (`sequencia.html:43`). O endpoint de sequência não inclui o
campo `diferenca` no objeto retornado (`main.py:210-220`); esse campo só existe no
retorno de `/similares?acordes` (`main.py:256-257`). Cada card mostra nome da
música, artista e gênero (`sequencia.html:51-53`) e abre a cifra ao ser clicado
(`sequencia.html:45`).

### 4.4 Lista de gêneros

O `select` de gênero usa `GENEROS`, uma constante hardcoded em
`static/assets/js/app.js:6-58` (51 gêneros), atribuída em
`sequencia.js:43`. O backend também expõe `GET /generos`
(`main.py:158-160`), que devolve os gêneros carregados do CSV; a página
`#/porsequencia` não chama esse endpoint.

## 5. Conexões entre componentes e fluxos de dados

### 5.1 Inicialização

1. `main.py` abre `data/top/dataset_final.csv` e lê a primeira linha
   (`main.py:49-50`). O arquivo não tem cabeçalho: a primeira linha é a música
   `14-bis,a-qualquer-tempo,...`, descartada por `f.readline()`. Por isso o app
   carrega 67.585 das 67.586 linhas de dados.
2. Para cada linha, remove aspas e `NA`, remove o último caractere e divide por
   vírgula (`main.py:52-55`).
3. Converte popularidade para inteiro (`main.py:56`), limpa a cifra com
   `limpa_cifra` (`main.py:58-61`) e separa `SEQ_FAMOSA` por `;`
   (`main.py:63`).
4. Cria `Musica(...)`, que calcula `acordes = list(set(cifra))` e monta
   `id_unico_musica`/`url` (`main.py:69-72`, `musica.py:16-22`).
5. Popula `musicas_dict`, `generos`, `acordes`, `genero_musicas`
   (`main.py:74-85`).
6. Ordena um `OrderedDict` global por popularidade (`main.py:88-89`), converte
   `generos` de `set` para lista (`main.py:92`) e ordena cada lista de gênero por
   popularidade (`main.py:95-96`).
7. Fecha o arquivo (`main.py:98`). Não há banco nem recarga por requisição.

### 5.2 Busca por sequência (fluxo atual)

```text
AngularJS #/porsequencia
  -> seleciona um dos 4 objetos hardcoded (sequencia.js:33-37)
  -> GET similares?sequencia=C,G,Am,F[&generos=...] (sequencia.js:72-77)
  -> Flask /similares (main.py:170-201)
  -> remove vírgulas: "CGAmF" (main.py:191)
  -> busca exata em `sequencias` (main.py:194)
  -> get_similares_por_sequencia(id_seq, generos_key) (main.py:195-196,203-223)
  -> filtra por gênero e por `str(id_seq) in musica.seqs_famosas` (main.py:205-209)
  -> monta dicts de resultado (main.py:210-221)
  -> get_pagina(..., pagina_tag) (main.py:226-228)
  -> json.dumps(...) (main.py:197)
  -> AngularJS recebe string JSON, exibe cards e ordena por popularidade no cliente
     (sequencia.html:42)
```

Características do fluxo:

- Sequência fora do dicionário de seis chaves não chega a `apply_filtro`: o
  endpoint retorna `[]` imediatamente (`main.py:192-197`).
- A paginação é feita no backend por slicing de 100 itens
  (`main.py:35,226-228`); a resposta não informa total nem página.
- O endpoint de sequência devolve `id_unico_musica`, `id_artista`, `id_musica`,
  `nome_artista`, `nome_musica`, `popularidade`, `acordes`, `genero` e `url`
  (`main.py:210-220`).
- Todos os endpoints usam `json.dumps`, não `jsonify`; a resposta sai como
  `text/html` (`AGENTS.md:46`; confirmado nas chamadas de teste).
- O CORS é aberto para qualquer origem por `@app.after_request`
  (`main.py:274-277`).

### 5.3 Busca por acordes (contraste)

`GET /similares?acordes=C,G` divide os acordes por vírgula
(`main.py:185-186`) e chama `get_similares`, que calcula
`set(acordes).intersection(set(musica.acordes))` e inclui qualquer música com
interseção não vazia (`main.py:236-260`). Não há ordem, sequência ou exigência de
todos os acordes. O frontend de `#/poracordes` monta essa chamada em
`static/assets/js/controllers/acordes.js:84-96`.

## 6. Arquivos-chave consultados

| arquivo | papel no estado atual |
|---|---|
| `main.py:11-98` | carga do CSV, `Musica`, índices de coluna, gêneros e dicionário de sequências |
| `main.py:170-228` | endpoint `/similares`, matching por tag e paginação |
| `main.py:230-272` | matching por interseção de acordes e filtro por gênero |
| `musica.py:1-25` | objeto `Musica`: `cifra` ordenada, `acordes` sem ordem/repetição, `seqs_famosas` |
| `scripts/generate_data_set.py:7-24` | geração da tag `SEQ_FAMOSA` |
| `scripts/normalize_chords.R:3-36` | normalização offline para graus, não usada pelo app |
| `scripts/simplify_chords.R:3-34` | simplificação offline para graus, não usada pelo app |
| `data/top/dataset_final.csv:1` | primeira linha de dados, descartada por `main.py:50` (o arquivo não tem cabeçalho) |
| `data/mapeamento_sequencias_famosas.txt:1-6` | nomes legíveis das seis sequências |
| `static/assets/js/routes.js:17-21` | rota `#/porsequencia` |
| `static/assets/js/controllers/sequencia.js:1-105` | catálogo hardcoded, busca e ações da página |
| `static/templates/sequencia.html:1-63` | painéis, gênero, resultados e clique nos cards |
| `static/assets/js/app.js:3-58` | constantes `RESTAPI` e `GENEROS` |
| `Dockerfile:1-12` | build/execução local, sem volume |
| `docs/adr/0001-local-only-docker-deploy.md:9-16` | decisão de container único local-only |
| `docs/adr/0002-persist-custom-sequences.md:1-8` | template de ADR de persistência ainda não preenchido |
| `baseline/seq1.json` … `baseline/seq6.json` | resultados de referência de execuções anteriores |
