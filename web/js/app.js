(function(){
	PNotify.prototype.options.styling = "bootstrap3";
	
	var app = angular.module('appTsw', [ 'appTsw.TvShowList', 'appTsw.Config', 'ui.bootstrap' ]);
	
	app.run(function($rootScope, $templateCache) {
	   $rootScope.$on('$viewContentLoaded', function() {
		  $templateCache.removeAll();
	   });
	});
	
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

$(document).on('change', '.btn-file :file', function() {
	console.log($(this).val());
  var input = $(this),
      numFiles = input.get(0).files ? input.get(0).files.length : 1,
      label = input.val().replace(/\\/g, '/').replace(/.*\//, '');
  input.trigger('fileselect', [numFiles, label]);
});

$(document).on('fileselect', '.btn-file :file', function(event, numFiles, label) {
        var input = $(this).parents('.input-group').find(':text'),
            log = numFiles > 1 ? numFiles + ' files selected' : label;
        
        if( input.length ) {
            input.val(log);
        } else {
            if( log ) alert(log);
        }
        
    });
