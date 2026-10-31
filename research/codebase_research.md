# Pesquisa do Codebase - deciframe/ciframe

## Resumo das Descobertas (3-6 sentenças)

O deciframe é uma ferramenta de descoberta musical para músicos que sugere músicas similares com base em acordes já conhecidos, títulos/artistas ou sequências famosas de acordes. O backend é um único arquivo Flask (`main.py`) que carrega todo o dataset `data/top/dataset_final.csv` em memória na inicialização (sem banco de dados), com instâncias da classe `Musica` (em `musica.py`). A API expõe endpoints REST que retornam JSON via `json.dumps()` com `Content-Type: text/html` (comportamento legado intencional). O frontend é AngularJS 1.4.9 estático servido pelo próprio Flask, com três modos de busca: por acordes, por música e por sequências famosas de acordes. O deploy é feito via Docker com gunicorn escutando na porta 8080.

## Componentes e Áreas Detalhadas

### 1) Backend - Classe `Musica`
**Arquivo:** `musica.py:1-25`

- `Musica.__init__(id_artista, nome_artista, id_musica, nome_musica, genero, popularidade, seqs_famosas, tom, cifra)` (`musica.py:3-21`): armazena atributos diretos, calcula `self.acordes = list(set(cifra))` (conjunto de acordes únicos da cifra), `self.id_unico_musica = '%s_%s' % (id_artista, id_musica)`, e `self.url = 'http://www.cifraclub.com.br/%s/%s' % (id_artista, id_musica)`.
- `__str__()` retorna `'%s,%s,%s' % (self.id_unico_musica, self.genero, self.popularidade)` (`musica.py:24-25`).

### 2) Backend - Inicialização e Carregamento de Dados
**Arquivo:** `main.py:9-98`

- App Flask: `app = Flask(__name__)` (`main.py:9`).
- Função `limpa_cifra(raw_cifra)` (`main.py:11-23`): para cada elemento em `raw_cifra`, se vazio ignora. Se contém `|` (tablatura), pega o primeiro token antes de `|` e espaço como acorde (`m.split('|')[0].split()[0]`) e adiciona. Caso contrário, divide por espaços e adiciona todos os tokens. Retorna lista de acordes.
- Constantes/índices das colunas CSV (`main.py:26-35`): `ARTISTA_ID=0, MUSICA_ID=1, ARTISTA=2, MUSICA=3, GENERO=4, POPULARIDADE=5, TOM=6, SEQ_FAMOSA=7, CIFRA=8, TAM_PAGINA=100`.
- Estruturas globais iniciais (`main.py:37-48`): `genero_musicas={}`, `generos=set()`, `acordes=set()`, `sequencias` com mapeamento de strings de sequência famosa para IDs (`'BmGDA':0, 'CGAmF':1, 'EmG':2, 'CA7DmG7':3, 'GmF':4, 'CC7FFm':5`), `musicas_dict={}`.
- Carregamento CSV (`main.py:49-98`): abre `data/top/dataset_final.csv`, lê cabeçalho (`f.readline()`), itera linhas. Para cada linha: remove aspas `"` e `NA`, remove último caractere (`[:-1]`), divide por vírgula. Converte `POPULARIDADE` para int removendo pontos. Se `CIFRA` vazia → `[]`, senão `limpa_cifra(musica[CIFRA].split(';'))`. `SEQ_FAMOSA` dividido por `;`. Adiciona gênero ao set `generos`. Cria `Musica(...)` com parâmetros na ordem: `musica[ARTISTA_ID], musica[ARTISTA], musica[MUSICA_ID], musica[MUSICA], musica[GENERO], int(musica[POPULARIDADE]), musica[SEQ_FAMOSA], musica[TOM], musica[CIFRA]` e armazena em `musicas_dict[musica_obj.id_unico_musica] = musica_obj`. Adiciona acordes únicos ao set `acordes` iterando `musica_obj.acordes`. Agrupa por gênero em `genero_musicas`. Após loop, constrói `musicas` como `OrderedDict` ordenado por `popularidade` reverso (`main.py:88-89`). Converte `generos` para lista (`main.py:92`). Ordena listas em `genero_musicas` por popularidade reverso por gênero (`main.py:95-96`). Fecha arquivo.
- Arquivo CSV utilizado: `data/top/dataset_final.csv` (cabeçalho observado: `14-bis,...` linhas iniciam com `id_artista,id_musica,...` conforme mostrado em `head`).

### 3) Backend - Rotas e Funções Auxiliares
**Arquivo:** `main.py:101-280`

- `GET /` (`main.py:101-103`): retorna `app.send_static_file('index.html')`.
- `GET /<path:path>` (`main.py:109-112`): proxy estático via `app.send_static_file(path)`.
- `GET /search` (`main.py:114-142`): busca por título/artista. Parâmetros: `generos` (opcional, lista separada por vírgula), `pagina` (default `'1'`), `key` (obrigatório). Normaliza `key` para minúsculas e aplica `remover_combinantes` (normalização NFD removendo caracteres com categoria `Mn`) dividindo por espaços. Define `generos_key = generos` (lista global) ou split de `generos_tag`. Filtra coleção com `apply_filtro(musicas.values(), generos_key)`. Para cada música, concatena `'%s %s' % (musica.nome_artista.lower(), musica.nome_musica.lower())`, normaliza com `remover_combinantes` e divide; inclui se `all(key in text_list for key in keys)`. Monta dict com `id_unico_musica, id_artista, id_musica, nome_artista, nome_musica, genero, url` e retorna `json.dumps(get_pagina(out, pagina_tag))`.
- `remover_combinantes(string)` (`main.py:145-147`): normalização Unicode NFD, remove diacríticos (categoria Mn).
- `GET /musicas` (`main.py:154-156`): retorna `json.dumps([v.__dict__ for v in musicas.values()])` (todas as músicas ordenadas por popularidade via OrderedDict).
- `GET /generos` (`main.py:158-160`): `json.dumps(generos)`.
- `GET /acordes` (`main.py:162-164`): `json.dumps(list(acordes))` (set convertido em lista).
- `GET /musica/<m_id>/` (`main.py:166-168`): retorna `json.dumps(musicas[m_id].__dict__)`.
- `GET /similares` (`main.py:170-201`): busca por similaridade. Parâmetros: `acordes` (opcional), `id_unico_musica` (opcional), `sequencia` (opcional), `pagina` (default `'1'`), `generos` (opcional). `generos_key` default lista global, ou split se fornecido. 
  - Se `acordes_tag`: `acordes = acordes_tag.split(',')`
  - Elif `id_musica_tag`: busca `musica = musicas[id_musica_tag]` e usa `acordes = musica.acordes`
  - Elif `sequencia_tag`: `acordes = sequencia_tag.replace(',','')` (concatena), busca se em `sequencias`; se sim obtém `id_seq`, chama `get_similares_por_sequencia(id_seq, generos_key)`, paginada com `get_pagina`, retorna `json.dumps(similares)`. 
  - Caso contrário (tem acordes por tag ou por música), chama `get_similares(acordes, generos_key, id_musica_tag)` e retorna paginado.
- `get_similares_por_sequencia(id_seq, generos_key)` (`main.py:203-223`): filtra com `apply_filtro(musicas.values(), generos_key)`, para cada música verifica se `str(id_seq) in musica.seqs_famosas` (comparação de string com elementos da lista). Se sim, constrói dict com campos similares aos de busca mas inclui `popularidade, acordes` e retorna lista.
- `get_pagina(colecao, pagina_tag)` (`main.py:226-228`): `sl = (int(pagina_tag)-1)*TAM_PAGINA; return colecao[sl:sl+TAM_PAGINA]` (paginação por slicing).
- `get_similares(acordes, generos_key, id_musica = None)` (`main.py:230-263`): filtra coleção com `apply_filtro`. Para cada música diferente de `id_musica` (se fornecido), calcula `inter = set(acordes).intersection(set(musica.acordes))` e `diff = set(musica.acordes) - set(acordes)`. Se `len(inter) > 0`, adiciona dict com `diferenca` (lista) e `intersecao` (lista). Ordenação final: `sorted(similares, key=lambda x: (len(x['diferenca']), -len(x['intersecao'])))` (menor diferença primeiro, maior interseção em caso de empate via -len).
- `apply_filtro(musicas, generos_key)` (`main.py:266-272`): para cada gênero em `generos_key`, se gênero em `generos` (lista global), concatena `genero_musicas[genero]` na coleção. Retorna coleção agregada (pode ter duplicados? não há deduplicação explícita; `genero_musicas` agrupa por gênero e uma música pertence a exatamente um gênero no CSV).
- CORS: `@app.after_request` adiciona `Access-Control-Allow-Origin: *` (`main.py:274-277`).
- Execução: `if __name__ == '__main__': app.run(debug=True)` (`main.py:279-280`).

### 4) Frontend - Configuração e Rotas
**Arquivo:** `static/assets/js/app.js:1-58`  
- Módulo `deciframeApp` com dependências `['ngRoute', 'ngAnimate', 'ngProgress', 'ui.bootstrap']` (`app.js:2`).
- Constante `RESTAPI.url = 'http://localhost:5003'` (`app.js:3-5`).
- Constante `GENEROS` com lista extensa de gêneros musicais (`app.js:6-58`).

**Arquivo:** `static/assets/js/routes.js:1-29`  
Rotas:
- `/` → `templates/home.html`, controller `HomeController` (`routes.js:3-6`)
- `/poracordes` → `templates/acordes.html`, controller `AcordesController`, `controllerAs: "Chords"` (`routes.js:7-11`)
- `/pormusica` → `templates/musica.html`, controller `MusicaController`, `controllerAs: "Musica"` (`routes.js:12-16`)
- `/porsequencia` → `templates/sequencia.html`, controller `SequenciaController`, `controllerAs: "Sequencia"` (`routes.js:17-21`)
- `/sobre` → `templates/about.html`, controller `AboutController` (`routes.js:22-25`)
- otherwise → redirect `/` (`routes.js:26-28`)

**Arquivo:** `static/index.html` (trechos relevantes)  
Carrega CDN: jQuery 1.11.3, Bootstrap 3.3.6, AngularJS 1.4.9 + ngRoute/ngAnimate, UI Bootstrap 2.1.4, `assets/js/ngprogress.js`, e app/scripts/controllers/directives: `app.js`, `routes.js`, `controllers/main.js`, `controllers/home.js`, `controllers/about.js`, `controllers/acordes.js`, `controllers/musica.js`, `controllers/sequencia.js`, `directives/df-hex.js`, `directives/df-esfinge.js`. Usa `ng-view`. Interface com logo e menu "sobre". (`static/index.html`)

### 5) Frontend - Controllers
**Arquivo:** `static/assets/js/controllers/home.js:1-4`  
`HomeController` define apenas `$scope.pageTitle='Home'`, `$scope.pageClass='page-home'`.

**Arquivo:** `static/assets/js/controllers/acordes.js:1-180`  
- Define listas de acordes agrupados por nota com cores (`acordesC/D/E/F/G/A/B`) (`acordes.js:2-56`).
- Inicializa `vm.acordes` com os grupos, `vm.meusAcordes=[]`, flags de busca, `vm.musics=[]`, `vm.generos=GENEROS`, `vm.meuGenero=""`, `vm.progressbar = ngProgressFactory.createInstance()` (`acordes.js:57-73`).
- `vm.addAcorde(acorde)`: adiciona se não existir, remove se já existir (toggle). Chama `vm.pesquisarPorAcordes()` (`acordes.js:75-82`).
- `vm.temAcorde(acorde)`: verifica presença (`acordes.js:83-85`).
- `createChordsString(chords)`: concatena `acorde` com vírgulas, remove última vírgula (`acordes.js:87-92`).
- `vm.pesquisarPorAcordes()`: se houver acordes, inicia progressbar, seta mensagem, limpa `vm.musics`, constrói `searchString = "similares?acordes=".concat(createChordsString(vm.meusAcordes))` e adiciona `&generos=` se `vm.meuGenero` não vazio. Faz `$http.get(apiUrl.concat(searchString))` onde `apiUrl` é vazio (usa caminho relativo). Em sucesso preenche `vm.musics`, atualiza flags; em erro seta mensagem de erro (`acordes.js:94-138`).
- `vm.goToLirics(music)`: `$window.open(music.url)` (`acordes.js:140-142`).
- `vm.goToResults()`: esconde contador e faz scroll para `#results` (`acordes.js:144-147`).

**Arquivo:** `static/assets/js/controllers/musica.js:1-200`  
- Inicializa `vm.acordes=[]`, `vm.minhaMusica={}`, flags, `vm.musics=[]`, `vm.generos=GENEROS`, `vm.meuGenero=""`, `vm.progressbar`, `var apiUrl=""` (`musica.js:2-13`).
- `vm.getMusicas(val)`: busca autocomplete com `search?key=` e retorna `response.data` (com progressbar) (`musica.js:15-20`).
- `vm.addAcorde`/`vm.temAcorde`/`createChordsString` presentes mas não usados diretamente no fluxo principal mostrado (`musica.js:22-41`).
- `vm.pesquisarPorMusica(musica)`: se fornecida atualiza `vm.minhaMusica`, inicia busca, monta `searchString = "similares?id_unico_musica=".concat(vm.minhaMusica.id_unico_musica)`, adiciona `&generos` se selecionado, faz GET para `apiUrl.concat(searchString)`. Atualiza UI em sucesso/erro (`musica.js:43-88`).
- `vm.goToLirics`, `vm.goToResults` similares (`musica.js:90-97`).

**Arquivo:** `static/assets/js/controllers/sequencia.js:1-160`  
- Define 4 sequências famosas pré-configuradas com acordes e cores (`sequencia1-4`) (`sequencia.js:2-38`).
- Inicializa arrays/objetos e flags (`sequencia.js:39-51`).
- `vm.temAcorde(acorde)`: verifica se acorde está em `vm.minhaSequencia.acordes` (`sequencia.js:53-59`).
- `createChordsString(chords)`: concatena com vírgulas (`sequencia.js:61-66`).
- `vm.pesquisarPorSequencia(sequencia)`: se fornecida atualiza `vm.minhaSequencia`, inicia busca, monta `searchString = "similares?sequencia=".concat(createChordsString(vm.minhaSequencia.acordes))`, adiciona `&generos` se presente, faz GET (`sequencia.js:68-110`).
- `vm.limparPesquisa()`: limpa `vm.minhaSequencia` e `vm.musics` (`sequencia.js:112-115`).
- `vm.goToLirics`, `vm.goToResults` similares (`sequencia.js:117-125`).

### 6) Infraestrutura, Deploy e Documentação
**Arquivo:** `Dockerfile:1-13`  
`FROM python:3.9-slim`, copia `requirements.txt`, instala com `--no-cache-dir`, copia tudo, expõe `8080`, comando `gunicorn --bind 0.0.0.0:8080 main:app`.

**Arquivo:** `requirements.txt:1-8`  
`Flask==3.1.3`, `gunicorn==23.0.0`.

**Arquivo:** `README.md:1-35`  
Descrição em português; stack Flask + AngularJS estático + CSV em memória; instruções Docker (`docker build -t ciframe . && docker run -p 8080:8080 ciframe`, acessa `:8080`) e virtualenv (`pip install -r requirements.txt && python main.py`, acessa `:5000`); referências a `CONTRIB.md` e `LICENSE`.

**Arquivo:** `AGENTS.md:1-47`  
Documentação para agentes: descreve propósito, stack (backend Python 3.9/Flask 3.1/gunicorn single `main.py` carregando CSV em memória, frontend AngularJS 1.4.9/jQuery sem build com freeze levantado, deploy local-only), execução Docker/venv, verificação com `curl http://localhost:8080/generos` (deve retornar array JSON), gotchas (CSV lido na importação requer restart, endpoints retornam `json.dumps()` como string → `Content-Type: text/html` intencional, checar `docs/adr/` para deploy).

**Outros arquivos relevantes observados:** `data/top/dataset_final.csv` (fonte de dados carregada em `main.py:49`), diretórios `static/templates/`, `static/assets/js/controllers/main.js`, `static/assets/js/directives/`, `docs/adr/`, `docs/features/`, `scripts/`, `baseline/`.

## Fluxos de Dados e Conexões Entre Componentes

### Fluxo 1: Inicialização da aplicação
1. `main.py` importado/executado → instancia `Flask(__name__)` (`main.py:9`).
2. Define funções utilitárias e constantes (`main.py:11-48`).
3. Abre e parseia `data/top/dataset_final.csv` linha por linha (`main.py:49-98`): para cada linha processa CSV (remove aspas/NA, converte popularidade), processa cifra via `limpa_cifra()` se não vazia, divide `SEQ_FAMOSA` por `;`, cria `Musica`, popula `musicas_dict`, atualiza `generos` set, atualiza `acordes` set, agrupa em `genero_musicas` por gênero.
4. Constrói `musicas` como `OrderedDict` ordenado por `popularidade` desc (`main.py:88-89`).
5. Converte `generos` para lista (`main.py:92`), ordena cada lista em `genero_musicas` por popularidade desc (`main.py:95-96`), fecha arquivo. Estado global pronto em memória.

### Fluxo 2: Busca por acordes (frontend → backend)
1. Usuário acessa rota `/poracordes` → `routes.js:7-11` carrega template/controller `AcordesController` (`static/assets/js/controllers/acordes.js`).
2. Usuário seleciona acordes via `vm.addAcorde(acorde)` que faz toggle em `vm.meusAcordes` e chama `vm.pesquisarPorAcordes()` (`acordes.js:75-82,94-138`).
3. Se houver acordes, constrói query: `similares?acordes=C,Am,...` (vírgulas) + opcional `&generos=Rock,...` usando `vm.meuGenero`. Chama `$http.get(apiUrl + searchString)` com `apiUrl` vazio (mesmo host/porta).
4. Backend em `main.py:170-201`: lê params, extrai `acordes_tag`, define `generos_key` (global ou split). Como tem `acordes_tag`, faz `acordes = acordes_tag.split(',')` (`main.py:185-186`). Chama `get_similares(acordes, generos_key, None)` (`main.py:199`), paginado com `get_pagina(..., pagina_tag)` e retorna `json.dumps(...)`.
5. `get_similares()` filtra por `apply_filtro(musicas.values(), generos_key)`, para cada música != `id_musica` calcula interseção/diferença entre sets de acordes, adiciona se `len(inter)>0` com `diferenca` e `intersecao`, ordena por `(len(diferenca), -len(intersecao))` (`main.py:230-263`).
6. Frontend recebe array JSON, exibe resultados, permite abrir URL com `vm.goToLirics()` → `$window.open(music.url)` que aponta para `http://www.cifraclub.com.br/...` gerado por `Musica` (`musica.py:22`).

### Fluxo 3: Busca por música (frontend → backend)
1. Rota `/pormusica` → `MusicaController` (`routes.js:12-16`, `musica.js`).
2. Autocomplete usa `vm.getMusicas(val)` chamando `search?key=...` (`musica.js:15-20`), backend em `main.py:114-142` faz busca por substring em nome do artista+nome da música após normalização Unicode, filtra por gêneros se fornecidos, pagina e retorna campos reduzidos.
3. Ao selecionar música, `vm.pesquisarPorMusica(musica)` monta `similares?id_unico_musica=<id>` + opcional `generos`, backend pega `musica = musicas[id_musica_tag]` e usa `acordes = musica.acordes` (`main.py:187-189`), chama `get_similares(acordes, generos_key, id_musica_tag)` (assim exclui a própria música pois `musica.id_unico_musica != id_musica` em `main.py:238`), retorna paginado.

### Fluxo 4: Busca por sequência famosa (frontend → backend)
1. Rota `/porsequencia` → `SequenciaController` com 4 sequências pré-definidas mapeadas para acordes (`sequencia.js:2-51`).
2. `vm.pesquisarPorSequencia(sequencia)` monta `similares?sequencia=C,G,Am,F` (concatena acordes com vírgula, depois backend faz `replace(',','')` para formar string concatena) (`sequencia.js:68-110`, `main.py:190-197`).
3. Backend: `acordes = sequencia_tag.replace(',','')`, verifica se existe em `sequencias` dict (`main.py:40-45`, `main.py:194`); se sim, obtém `id_seq`, chama `get_similares_por_sequencia(id_seq, generos_key)`, filtra por `str(id_seq) in musica.seqs_famosas` e retorna paginado.

### Conexões transversais
- **Estado global compartilhado:** todos os endpoints leem de estruturas globais carregadas na inicialização (`musicas`, `musicas_dict`, `genero_musicas`, `generos`, `acordes`, `sequencias`) — sem acesso a banco. Mudanças em CSV exigem restart (`AGENTS.md:45`).
- **Normalização de texto:** `remover_combinantes()` usada em busca por chave (`main.py:119,130,145-147`).
- **Processamento de cifras:** `limpa_cifra()` em inicialização (`main.py:11-23,58-61`) transforma string CSV em lista de acordes; `Musica.acordes` armazena `set(cifra)` (únicos).
- **Respostas API:** todos endpoints usam `json.dumps()` diretamente (não `jsonify`), retornando string JSON com `Content-Type: text/html` por padrão (`AGENTS.md:46`, `main.py:142,156,160,164,168,197,201`).
- **CORS:** `@app.after_request` adiciona header permissivo (`main.py:274-277`).
- **Paginação:** `TAM_PAGINA=100` e `get_pagina()` por slicing em todas as listagens de resultados (`main.py:35,226-228`).
- **URLs externas:** `Musica.url` aponta para `http://www.cifraclub.com.br/...` e frontend abre com `window.open()` (`musica.py:22`, controllers).
- **Serviço de arquivos estáticos:** Flask serve index e assets; `app.send_static_file` usado (`main.py:102,111`).
- **Deploy:** gunicorn em `0.0.0.0:8080` via Dockerfile; em dev com `python main.py` roda em porta padrão Flask 5000 (`README.md:15-31`, `Dockerfile:11`, `AGENTS.md:32`).
