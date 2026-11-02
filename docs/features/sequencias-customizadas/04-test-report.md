# Relatório de testes — Sequências de Acordes Customizadas

## Cobertura

- `tests/test_matching.py`: matcher token a token — caso exato, caixa, bloco
  contíguo, ordem invertida, repetição interna, repetição fora do bloco, acorde
  extra e cifra vazia.
- `tests/test_sequencias_db.py`: schema/seed das 6 originais, idempotência do
  seed, criação sem nome, duplicata ignorando caixa, busca canônica, persistência
  entre conexões e uso de `SEQUENCES_DB`.
- `tests/test_api.py`: `GET /sequencias`, `POST /sequencias` com e sem nome,
  payloads inválidos (`400`), duplicata de original e de sequência nova (`409`),
  busca das originais, caixa ignorada, forma concatenada retornando `[]`,
  sequência desconhecida e sequência nova encontrando música.
- Total: 29 testes automatizados, todos passando.

## Teste de regressão obrigatório

`python scripts/check_sequence_regression.py` comparou a regra executada em
`musica.cifra` com as tags `SEQ_FAMOSA` e os baselines:

```
seq0 (Sequência de Bm): esperado=199 encontrado=199 baseline=100
seq1 (Sequência de C): esperado=296 encontrado=296 baseline=100
seq2 (Sequência Em): esperado=4 encontrado=4 baseline=4
seq3 (Sequência de C (Samba)): esperado=5 encontrado=5 baseline=5
seq4 (Sequência de Gm): esperado=7 encontrado=7 baseline=7
seq5 (Sequência de C (Samba cont.)): esperado=3 encontrado=3 baseline=3
OK
```

Os conjuntos de ids das 6 sequências batem exatamente com `SEQ_FAMOSA`.
`baseline/seq1.json` e `seq2.json` são páginas históricas: todos os ids estão
contidos no conjunto completo atual, mas a primeira página atual mudou com a
ordenação/popularidade. `seq3`–`seq6` continuam batendo integralmente.

Também foi verificado manualmente com gunicorn e com Docker:

- `POST /sequencias` retornou `201` e a sequência apareceu em `GET /sequencias`;
- repetir os mesmos acordes com outra caixa/nome retornou `409`;
- `/similares?sequencia=Bm,G,D,A` e `bm,g,d,a` retornaram os mesmos 100 ids da
  primeira página;
- `/similares?sequencia=BmGDA` retornou `[]`;
- após remover o container e subir outro com o mesmo volume `ciframe-test-data`,
  o catálogo continuou com a sequência criada.

## Ajustes de UI da página `#/porsequencia`

Verificado com Chrome headless via DevTools Protocol, sem alterar API nem
matching:

- em larguras de `1280px`, `1024px` e `768px` o painel começa abaixo da faixa do
  logo (painel em `top: 70px`), a lista rola em um container próprio e o botão
  "Cadastrar sequência" permanece visível no cabeçalho fixo;
- em `1280px`, o nome e os acordes começam no mesmo `left` (delta `0`), com
  `28px` de margem e `24px` de separação visual entre sequências;
- com `400` e `409`, o formulário permanece aberto e mantém nome, acordes e
  mensagem de erro; no sucesso, fecha, limpa os campos e mantém o alerta de
  sucesso; em cancelar, fecha e limpa campos e mensagens;
- a área de resultados mostra a mensagem de boas-vindas quando não há sequência
  selecionada; ela some ao selecionar, volta ao limpar a pesquisa e permanece
  oculta quando uma busca selecionada não retorna músicas;
- em `767x800`, `375x800` e `320x800` o layout empilha, a página rola, o logo sai
  da tela com a rolagem, não há overflow horizontal e os campos/ações cabem na
  largura disponível.

## Como rodar

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/check_sequence_regression.py
```

O teste de API usa um banco temporário via `SEQUENCES_DB`; o script de regressão
também usa um SQLite temporário quando a variável não está definida.

## O que ficou de fora

- Teste visual automatizado com baseline de screenshots e validação em múltiplos
  navegadores: a página foi exercitada em Chrome headless via DevTools Protocol,
  mas não há comparação de imagens nem cobertura cross-browser.
- Teste de carga/concorrência e rate limiting: fora do escopo desta entrega.
- Migração de um banco anterior: não existe catálogo SQLite legado para migrar.
- Normalização enarmônica/sufixos e edição/exclusão de sequências: decisões
  explícitas de escopo, não lacunas de teste.
