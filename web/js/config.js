(function(){
	var app = angular.module('appTsw.Config', [  ]);
	
	app.controller('TorrentProvidersController', [ '$element', function($element){
		$element.alpaca(alpacaForm("torrentSearch"));
	}]);
	
	app.controller('TorrentClientController', [ '$element', function($element){
		$element.alpaca(alpacaForm("downloader"));
	}]);
	
	app.controller('TransferController', [ '$element', function($element){
		$element.alpaca(alpacaForm("transferer"));
	}]);
	
	app.controller('NotificatorController', [ '$element', function($element){
		$element.alpaca(alpacaForm("notificator"));
	}]);
})();
