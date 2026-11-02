angular.module('deciframeApp').controller('SequenciaController', function($http, $window, ngProgressFactory, $anchorScroll, $location, GENEROS) {
  var COR_SEQUENCIA = '#2E1C74';
  var vm = this;
  vm.sequenciasFamosas = [];
  vm.minhaSequencia = {};
  vm.novaSequencia = { 'nome': '', 'acordes': '' };
  vm.formularioAberto = false;
  vm.erroCadastro = '';
  vm.sucessoCadastro = '';
  vm.erroCatalogo = '';
  vm.isSearching = false;
  vm.showSearchResultsCount = false;
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

    vm.progressbar.start();
    vm.esfigeSpeech = "Procurando músicas com base na sequencia...";
    vm.isSearching = true;
    vm.musics = [];

    var apiUrl = "";
    var searchString = "similares?sequencia=".concat(
      encodeURIComponent(createChordsString(vm.minhaSequencia.acordes)));
    if (vm.meuGenero !== "" && vm.meuGenero !== null) {
      searchString += "&generos=" + encodeURIComponent(vm.meuGenero);
    }
    $http.get(apiUrl.concat(searchString))
      .success(function(data) {
        vm.progressbar.complete();
        vm.esfigeSpeech = "Encontrei essas músicas";
        vm.isSearching = false;
        vm.showSearchResultsCount = true;
        vm.musics = data;
      })
      .error(function(data) {
        vm.esfigeSpeech = "Ops! Algo errado.";
        vm.isSearching = false;
        vm.showSearchResultsCount = false;
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

    var nome = (vm.novaSequencia.nome || '').trim();
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
    vm.minhaSequencia = {};
    vm.musics = [];
    vm.esfigeSpeech = "";
    vm.showSearchResultsCount = false;
  };

  vm.goToLirics = function(music) {
    $window.open(music.url);
  };

  vm.goToResults = function() {
    vm.showSearchResultsCount = false;
    $("body").animate({scrollTop: $("#results").offset().top}, "slow");
  };
});
