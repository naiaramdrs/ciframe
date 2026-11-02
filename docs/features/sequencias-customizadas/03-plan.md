# Plano — Sequências de Acordes Customizadas

## Passos

1. [ ] Criar `matching.py` com a função pura de matching: normalização de caixa,
   bloco contíguo de tokens em `musica.cifra`, preservação de ordem/repetições e
   validação de que todos os acordes da música pertencem à sequência.
2. [ ] Criar testes unitários do matcher com `unittest` para caixa, ordem invertida,
   repetição interna, repetição fora do bloco, acorde extra e acorde desconhecido.
3. [ ] Criar `sequencias_db.py` com schema SQLite, seed idempotente das 6
   sequências (ids 0–5) usando nomes e acordes de
   `data/mapeamento_sequencias_famosas.txt:1-6`, listagem, criação e busca por
   `acordes_norm`.
4. [ ] Testar o banco em arquivo temporário: seed, ids, nome nulo, duplicata
   canônica e busca por sequência.
5. [ ] Integrar o banco ao startup de `main.py` com `SEQUENCES_DB` (padrão local
   `instance/deciframe.db` e `/data/deciframe.db` no Docker), mantendo
   músicas/gêneros no CSV em memória e preservando a paginação/filtro de gênero
   atuais. Criar a pasta do banco se ela não existir e adicionar `instance/` ao
   `.gitignore` e ao `.dockerignore`. Nos testes de API, definir um `SEQUENCES_DB`
   temporário antes de importar `main.py`, para não gravar no banco real.
6. [ ] Substituir o dicionário fixo e a consulta a `seqs_famosas` pelo lookup no
   banco + matcher em tempo real; manter `SEQ_FAMOSA` apenas para regressão.
   `/similares` passa a aceitar acordes separados por vírgula, ignorar caixa e
   deixar de reconhecer a forma concatenada (`BmGDA`), que retorna `[]`.
7. [ ] Implementar `GET /sequencias` (id, nome, acordes, criado_em) e
   `POST /sequencias` com `json.dumps`, validação de pelo menos 2 acordes sem
   vazios/espaços/vírgulas (`400`), nome opcional e duplicata ignorando caixa e
   sem considerar o nome (`409`). Acordes fora do dataset são aceitos.
8. [ ] Criar `scripts/check_sequence_regression.py` e validar a regra token a
   token sobre `musica.cifra`, chamando `/similares` em todas as páginas:
   counts 199/296/4/5/7/3 e todos os ids contra `SEQ_FAMOSA`. Usar `baseline/seq1.json`/`seq2.json` apenas como
   primeira página e `seq3.json`–`seq6.json` como referência completa.
9. [ ] Atualizar `sequencia.js` para carregar o catálogo, mapear acordes para
   `{acorde, cor}`, dividir e remover espaços ao redor dos separadores do
   formulário, enviar `POST`, recarregar após `201` e codificar os acordes na URL
   com `encodeURIComponent`.
10. [ ] Atualizar `sequencia.html` com o formulário, validação no cliente do
    mínimo de 2 acordes, mensagens de `400`/`409` e exibição dos acordes quando
    `nome` for nulo, mantendo a busca e os resultados atuais.
11. [ ] Adicionar `ENV SEQUENCES_DB=/data/deciframe.db` e `VOLUME /data` ao
    `Dockerfile`; documentar o `docker run -v deciframe-data:/data` e o padrão local
    `instance/deciframe.db` de `SEQUENCES_DB` em `README.md` e `AGENTS.md`.
12. [ ] Rodar testes de API, regressão, persistência com volume e checklist manual
    no browser; preencher `04-test-report.md` com as evidências.

**Estimativa total:** 2–3 dias de trabalho focado.

## Arquivos afetados

| Arquivo | Mudança |
|---|---|
| `matching.py` (novo) | Função pura de matching token a token; detalhe de implementação da regra da proposta |
| `sequencias_db.py` (novo) | Schema, seed, listagem, criação e busca por `acordes_norm` |
| `main.py` | Integrar SQLite, remover dicionário/tag do fluxo, ajustar `/similares` e criar `GET/POST /sequencias` |
| `musica.py` | Sem mudança; `cifra` já preserva ordem e repetição |
| `Dockerfile` | `ENV SEQUENCES_DB=/data/deciframe.db` e `VOLUME /data` |
| `.gitignore`, `.dockerignore` | Ignorar `instance/`, onde fica o banco local |
| `README.md` | Execução com volume nomeado e padrão local `instance/deciframe.db` de `SEQUENCES_DB` |
| `AGENTS.md` | Comando de execução, volume e caminho local do banco |
| `static/assets/js/controllers/sequencia.js` | Catálogo dinâmico, formulário, trim e encoding da URL |
| `static/templates/sequencia.html` | Formulário, mensagens de erro/sucesso e fallback de nome |
| `tests/test_matching.py` (novo) | Casos unitários do matcher |
| `tests/test_api.py` (novo) | Endpoints, validação, duplicatas e persistência |
| `scripts/check_sequence_regression.py` (novo) | Regressão contra `SEQ_FAMOSA` e baselines |
| `docs/features/sequencias-customizadas/04-test-report.md` | Preencher após os testes |

Sem alteração em `requirements.txt`, `data/` ou `baseline/`;
`data/mapeamento_sequencias_famosas.txt` é apenas lido no seed, e o banco local é
criado em `instance/`.

## Riscos e mitigação

- **Recall baixo para sequências novas:** pode retornar poucas ou nenhuma música.
  Detecção: teste com sequência válida fora das 6. Mitigação: registrar como
  limitação aceita e explicar na UI/teste, sem relaxar a regra das originais.
- **Regressão nas 6 sequências:** ids ou counts podem mudar. Detecção:
  `check_sequence_regression.py` contra `SEQ_FAMOSA`, comparando todas as páginas e
  usando os baselines apenas como referência de primeira página. Mitigação: não
  comparar ordem de página e bloquear a entrega se houver divergência.
- **Mudança de contrato da URL:** `BmGDA` deixa de funcionar. Detecção: teste da
  forma concatenada retornando `[]`. Mitigação: documentar a mudança e manter o
  frontend enviando acordes separados por vírgula.
- **Duplicatas ou diferenças de caixa:** a mesma sequência pode entrar duas vezes.
  Detecção: testes `Bm,G` vs `bm,g`, inclusive com nomes diferentes. Mitigação:
  `acordes_norm` canônico com `UNIQUE` e resposta `409`.
- **Perda do catálogo ao recriar o container:** arquivo SQLite fica na camada
  gravável. Detecção: remover o container e subir outro sem volume. Mitigação:
  `VOLUME /data`, volume nomeado e teste de persistência stop/start/recriação.
- **Payload inválido ou abusivo:** cadastro anônimo pode gravar lixo. Detecção:
  testes de 1 acorde, item vazio, item com espaço e item com vírgula. Mitigação:
  validação server-side com `400`; rate limiting fica fora do escopo.
- **Falha no frontend legado:** GET/POST ou caracteres como `#`/`+` podem quebrar o
  controller/URL. Detecção: checklist no browser com catálogo seed, cadastro,
  erro e acorde com `#`. Mitigação: estados de erro explícitos, recarga após `201`
  e `encodeURIComponent` na busca.
- **Concorrência de escrita no SQLite:** múltiplos requests podem disputar o
  arquivo. Detecção: teste de cadastros concorrentes. Mitigação: transações curtas
  e o gunicorn atual sem `--workers`.
- **Seed sobrescrever dados:** reiniciar o app pode duplicar ou alterar as 6.
  Detecção: reiniciar duas vezes e conferir ids. Mitigação: seed idempotente com
  `INSERT OR IGNORE` por id/chave canônica.
- **Desempenho da varredura:** cada busca percorre ~67.585 músicas. Detecção:
  medir tempo no teste. Mitigação: manter a varredura simples nesta entrega e
  registrar cache/índice como melhoria futura.

## Definição de pronto

- [ ] `POST /sequencias` cria uma sequência válida e retorna `201`; `nome` é
      opcional e pode ficar `NULL`.
- [ ] Cadastro com menos de 2 acordes, vazio, com espaço ou com vírgula retorna
      `400`.
- [ ] Duplicata ignorando caixa e sem considerar o nome retorna `409`.
- [ ] `GET /sequencias` lista as 6 originais e as novas com `id`, `nome`,
      `acordes` e `criado_em`.
- [ ] Busca por sequência nova funciona pelo mesmo `GET /similares`; `Bm,G,D,A` e
      `bm,g,d,a` encontram a mesma sequência, e `BmGDA` retorna `[]`.
- [ ] Acordes fora do dataset são aceitos no cadastro.
- [ ] As 6 originais mantêm os mesmos counts (199/296/4/5/7/3) e os mesmos
      conjuntos de ids em todas as páginas, com 0 divergências contra `SEQ_FAMOSA`.
- [ ] A regra token a token sobre `musica.cifra` foi validada, não apenas a réplica
      da string bruta do CSV.
- [ ] `SEQ_FAMOSA` não é consultada no fluxo de busca em produção.
- [ ] `#/porsequencia` lista o catálogo real, permite cadastrar, exibe erros,
      mostra acordes quando não há nome e codifica a URL da busca; uma sequência
      com `#` ou `+` é encontrada pela busca.
- [ ] Catálogo sobrevive a `docker stop/start` e à recriação com o mesmo volume.
- [ ] Endpoints continuam com `json.dumps` e `Content-Type: text/html`, e
      `/similares` mantém o mesmo formato de resposta.
- [ ] `04-test-report.md` registra os testes e o resultado da regressão.
