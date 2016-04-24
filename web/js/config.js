(function(){
	var app = angular.module('appTsw.Config', [  ]);
	
	app.controller('TorrentProvidersController', [ '$element', function($element){
		$element.alpaca(alpacaForm("torrentSearch"));
		console.log($element);
	}]);
	
	app.controller('TorrentClientController', [ '$element', function($element){
		$element.alpaca(alpacaForm("downloader"));
		console.log($element);
	}]);
	
	app.controller('TransferController', [ '$element', function($element){
		$element.alpaca(alpacaForm("transferer"));
		console.log($element);
	}]);
})();
