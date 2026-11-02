angular.module('deciframeApp').controller('SequenciaController', function($http, $window, ngProgressFactory, $anchorScroll, $location, GENEROS) {
  var COR_SEQUENCIA = '#2E1C74';
  var MAX_NOME_SEQUENCIA = 120;
  var MAX_ACORDES_SEQUENCIA = 50;
  var MAX_CARACTERES_ACORDE = 20;
  var buscaAtual = 0;
  var vm = this;
  vm.corSequencia = COR_SEQUENCIA;
  vm.sequenciasFamosas = [];
  vm.minhaSequencia = {};
  vm.novaSequencia = { 'nome': '', 'acordes': '' };
  vm.formularioAberto = false;
  vm.erroCadastro = '';
  vm.sucessoCadastro = '';
  vm.erroCatalogo = '';
  vm.isSearching = false;
  vm.showSearchResultsCount = false;
  vm.buscaSemResultados = false;
  vm.esfigeSpeech = "";
  vm.musics = [];
  vm.generos = GENEROS;
  vm.meuGenero = "";
  vm.progressbar = ngProgressFactory.createInstance();

  var sequenciaParaViewModel = function(sequencia) {
    return {
      'id': sequencia.id,
      'nome': sequencia.nome,
      'acordes': (sequencia.acordes || []).map(function(acorde) {
        return { 'acorde': acorde, 'cor': COR_SEQUENCIA };
      })
    };
  };

  var carregarSequencias = function() {
    vm.erroCatalogo = '';
    $http.get('sequencias')
      .success(function(data) {
        vm.sequenciasFamosas = data.map(sequenciaParaViewModel);
      })
      .error(function() {
        vm.erroCatalogo = 'Não foi possível carregar o catálogo de sequências.';
      });
  };

  carregarSequencias();

  vm.temAcorde = function(acorde) {
    if (vm.minhaSequencia.acordes) {
      return (vm.minhaSequencia.acordes.indexOf(acorde) > -1);
    } else {
      return false;
    }
  };

  var createChordsString = function(chords) {
    var str = "";
    for (var i = 0; i < chords.length; i++) {
      str = str.concat(chords[i].acorde, ',');
    }
    return str.substring(0, str.length-1);
  };

  vm.nomeSequencia = function(sequencia) {
    return sequencia.nome || createChordsString(sequencia.acordes);
  };

  vm.pesquisarPorSequencia = function(sequencia) {
    if (sequencia) {
      vm.minhaSequencia = sequencia;
    }
    if (!vm.minhaSequencia.acordes || vm.minhaSequencia.acordes.length === 0) {
      return;
    }

    var buscaId = ++buscaAtual;
    vm.progressbar.start();
    vm.esfigeSpeech = "Procurando músicas com base na sequencia...";
    vm.isSearching = true;
    vm.buscaSemResultados = false;
    vm.showSearchResultsCount = false;
    vm.musics = [];

    var apiUrl = "";
    var searchString = "similares?sequencia=".concat(
      encodeURIComponent(createChordsString(vm.minhaSequencia.acordes)));
    if (vm.meuGenero !== "" && vm.meuGenero !== null) {
      searchString += "&generos=" + encodeURIComponent(vm.meuGenero);
    }
    $http.get(apiUrl.concat(searchString))
      .success(function(data) {
        if (buscaId !== buscaAtual) {
          return;
        }

        var resultados = angular.isArray(data) ? data : [];
        vm.progressbar.complete();
        vm.isSearching = false;
        vm.musics = resultados;
        vm.buscaSemResultados = resultados.length === 0;

        if (vm.buscaSemResultados) {
          vm.esfigeSpeech = "Nenhuma música encontrada";
          vm.showSearchResultsCount = false;
        } else {
          vm.esfigeSpeech = "Encontrei essas músicas";
          vm.showSearchResultsCount = true;
        }
      })
      .error(function() {
        if (buscaId !== buscaAtual) {
          return;
        }

        vm.progressbar.complete();
        vm.esfigeSpeech = "Ops! Algo errado.";
        vm.isSearching = false;
        vm.showSearchResultsCount = false;
        vm.buscaSemResultados = false;
        vm.musics = [];
      });
  };

  vm.abrirFormulario = function() {
    vm.formularioAberto = true;
    vm.erroCadastro = '';
    vm.sucessoCadastro = '';
  };

  vm.cancelarCadastro = function() {
    vm.formularioAberto = false;
    vm.novaSequencia = { 'nome': '', 'acordes': '' };
    vm.erroCadastro = '';
    vm.sucessoCadastro = '';
  };

  vm.cadastrarSequencia = function() {
    vm.erroCadastro = '';

    var acordes = (vm.novaSequencia.acordes || '').split(',')
      .map(function(acorde) { return acorde.trim(); });

    if (acordes.length < 2 || acordes.some(function(acorde) { return !acorde; })) {
      vm.erroCadastro = 'Informe pelo menos 2 acordes separados por vírgula.';
      return;
    }

    if (acordes.length > MAX_ACORDES_SEQUENCIA) {
      vm.erroCadastro = 'Informe no máximo ' + MAX_ACORDES_SEQUENCIA + ' acordes.';
      return;
    }

    if (acordes.some(function(acorde) {
      return acorde.length > MAX_CARACTERES_ACORDE;
    })) {
      vm.erroCadastro = 'Cada acorde deve ter no máximo ' + MAX_CARACTERES_ACORDE + ' caracteres.';
      return;
    }

    var nome = (vm.novaSequencia.nome || '').trim();
    if (nome.length > MAX_NOME_SEQUENCIA) {
      vm.erroCadastro = 'O nome deve ter no máximo ' + MAX_NOME_SEQUENCIA + ' caracteres.';
      return;
    }

    $http.post('sequencias', { 'nome': nome || null, 'acordes': acordes })
      .success(function() {
        vm.formularioAberto = false;
        vm.sucessoCadastro = 'Sequência cadastrada com sucesso.';
        vm.novaSequencia = { 'nome': '', 'acordes': '' };
        carregarSequencias();
      })
      .error(function(data, status) {
        if (status === 409) {
          vm.erroCadastro = 'Essa sequência já está cadastrada.';
        } else if (status === 400) {
          vm.erroCadastro = 'Dados inválidos. Use pelo menos 2 acordes, separados por vírgula e sem espaços.';
        } else {
          vm.erroCadastro = 'Não foi possível cadastrar a sequência.';
        }
      });
  };

  vm.limparPesquisa = function() {
    buscaAtual++;
    vm.progressbar.complete();
    vm.minhaSequencia = {};
    vm.musics = [];
    vm.esfigeSpeech = "";
    vm.isSearching = false;
    vm.showSearchResultsCount = false;
    vm.buscaSemResultados = false;
  };

  vm.goToLirics = function(music) {
    $window.open(music.url);
  };

  vm.goToResults = function() {
    vm.showSearchResultsCount = false;
    $("body").animate({scrollTop: $("#results").offset().top}, "slow");
  };
});
