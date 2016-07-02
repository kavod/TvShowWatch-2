(function(){
	var app = angular.module('appTsw.Config', [  ]);

	app.controller('TorrentProvidersController', [ '$element', '$http', '$scope',function($element,$http,$scope){
		this.content = '';
		this.hide = true;
		this.isOpen = false;
		TPCtrl = this;
		$element.find('.alpacaForm').alpaca(alpacaForm("torrentSearch"));

		$scope.updateConfTest = function(isOpen) {
			isOpen = typeof isOpen !== 'undefined' ? isOpen : true;
			$http.get('/update/torrentSearch/confTest')
			.success(function(data){
				if (data === null)
				{
					TPCtrl.hide = true;
				} else {
					TPCtrl.hide = false;
					TPCtrl.content = data['content'];
					TPCtrl.type = (data['success']) ? 'panel-success' : 'panel-danger';
					TPCtrl.isOpen = isOpen;
					if (!data['success'])
					{
						$('#notification').scope().alert_error({error:"Configuration test of torrentSearch failed!",status:400});
					}
				}
			});
		};

		$scope.updateConfTest(isOpen=false);
	}]);

	app.controller('TorrentClientController', [ '$element', '$http', '$scope', function($element,$http,$scope){
		this.content = '';
		this.hide = true;
		this.isOpen = false;
		TCCtrl = this;
		$element.find('.alpacaForm').alpaca(alpacaForm("downloader"));

		$scope.updateConfTest = function(isOpen) {
			isOpen = typeof isOpen !== 'undefined' ? isOpen : true;
			$http.get('/update/downloader/confTest')
			.success(function(data){
				if (data === null)
				{
					TCCtrl.hide = true;
				} else {
					TCCtrl.hide = false;
					TCCtrl.content = data['content'];
					TCCtrl.type = (data['success']) ? 'panel-success' : 'panel-danger';
					TCCtrl.isOpen = isOpen;
					if (!data['success'])
					{
						$('#notification').scope().alert_error({error:"Configuration test of Downloader failed!",status:400});
					}
				}
			});
		};

		$scope.updateConfTest(isOpen=false);
	}]);

	app.controller('TransferController', [ '$element', function($element){
		$element.alpaca(alpacaForm("transferer"));
	}]);

	app.controller('NotificatorController', [ '$element', function($element){
		$element.alpaca(alpacaForm("notificator"));
	}]);
})();
