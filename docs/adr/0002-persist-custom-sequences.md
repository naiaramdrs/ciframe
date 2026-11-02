# Persistir sequências customizadas em SQLite no container único

A busca por sequência dependia de seis combinações fixas em `main.py` e de uma tag `SEQ_FAMOSA` pré-computada no CSV, enquanto o frontend mantinha apenas quatro sequências hardcoded. A nova feature exige cadastro anônimo e um catálogo que sobreviva a reinícios, o que não é atendido mantendo as sequências em memória ou no CSV.

Decidimos introduzir SQLite para persistir apenas o catálogo de sequências, semeando as seis originais e passando a calcular o matching em tempo real com a mesma regra para todas. O catálogo de músicas e gêneros continua vindo do CSV em memória. SQLite foi escolhido por ser biblioteca padrão, usar um único arquivo, oferecer restrição de unicidade e caber no container local-only sem serviço externo. TinyDB foi descartado por adicionar uma dependência sem restrição de unicidade nativa, `shelve`/`dbm` por não terem schema nem `UNIQUE`, e bancos cliente-servidor, como PostgreSQL e MySQL, por exigirem um serviço externo.

O container passa a exigir um volume nomeado para o arquivo do banco; sem ele, o catálogo se perde ao recriar o container. A limitação aceita é que sequências novas podem retornar poucas músicas, e o banco guarda somente o catálogo: não há login, edição ou exclusão. A tag `SEQ_FAMOSA` permanece no CSV apenas como referência para a regressão.
