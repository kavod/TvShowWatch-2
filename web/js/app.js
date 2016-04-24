(function(){
	PNotify.prototype.options.styling = "bootstrap3";
	
	var app = angular.module('appTsw', [ 'appTsw.TvShow', 'appTsw.Config', 'ui.bootstrap' ]);
	
	app.controller('TabsController', function(){
		this.tab = 'tvShows';
		this.selectTab = function(setTab) {
			this.tab = setTab;
		};
		this.isSelected = function(checkTab) {
			return this.tab === checkTab;
		};
	});
	
	app.controller('PillsController', function(){
		this.tab = 'torrent-search';
		this.selectTab = function(setTab) {
			this.tab = setTab;
		};
		this.isSelected = function(checkTab) {
			return this.tab === checkTab;
		};
	});
	
	app.controller('NotificationController',['$scope',function($scope) {
		$scope.alert_error = function(except) {
			new PNotify({
				title: 'Error',
				text: except.error + ' (' + except.status.toString() + ')',
				type: 'error'
			});
		}

		$scope.alert_success = function(except) {
			new PNotify({
				title: 'Success',
				text: except.error,
				type: 'success'
			});
		}
	}]);
	
	app.controller('TypeaheadController', ['$scope','$http', function($scope, $http) {
		$scope.getLivesearch = function(val) {
			return $http.get('/livesearch/' + val)
				.then(function(response){
					console.log(response.data);
					return response.data.map(function(item) {
						return {
							"seriesid":item.id,
							"title":item.value,
							"info":item.info
						}
					});
			});
		};
	}]);
	
})();