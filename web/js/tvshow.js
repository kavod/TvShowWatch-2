(function(){
	var app = angular.module('appTsw.TvShow', [ 'ngAnimate', 'ui.bootstrap' ]);

	app.controller('TvShowController', [ '$http', '$scope', 'fileUpload', function($http,$scope,fileUpload){

		this.data = $scope.tvshow;

		this.updateEpisode = function(seriesid) {
			var newvalue = {};
			newvalue = {tvShowID:parseInt($scope.tvshow.seriesid)};
			newvalue.season = parseInt($scope.tvshow.season);
			newvalue.episode = parseInt($scope.tvshow.episode);
			this.update(newvalue);
		};

		this.updatePattern = function() {
			var newvalue = {};
			newvalue = {tvShowID:parseInt($scope.tvshow.seriesid)};
			newvalue.pattern = $scope.tvshow.pattern;
			this.update(newvalue);
		};

		this.addKeyword = function() {
			var newvalue = {};
			newvalue = {tvShowID:parseInt($scope.tvshow.seriesid)};
			$scope.tvshow.keywords.push($scope.tvshow.newKeyword);
			newvalue.keywords = $scope.tvshow.keywords;
			delete($scope.tvshow.newKeyword);
			this.update(newvalue);
		};

		this.deleteKeyword = function(keyword) {
			var newvalue = {};
			newvalue = {tvShowID:parseInt($scope.tvshow.seriesid)};
			var index = $scope.tvshow.keywords.indexOf(keyword);
			if (index > -1) {
				$scope.tvshow.keywords.splice(index, 1);
			}
			newvalue.keywords = $scope.tvshow.keywords;
			this.update(newvalue);
		};

		this.addEmail = function() {
			var newvalue = {};
			newvalue = {tvShowID:parseInt($scope.tvshow.seriesid)};
			$scope.tvshow.emails.push($scope.tvshow.newEmail);
			newvalue.emails = $scope.tvshow.emails;
			delete($scope.tvshow.newEmail);
			this.update(newvalue);
		};

		this.deleteEmail = function(email) {
			var newvalue = {};
			newvalue = {tvShowID:parseInt($scope.tvshow.seriesid)};
			var index = $scope.tvshow.emails.indexOf(email);
			if (index > -1) {
				$scope.tvshow.emails.splice(index, 1);
			}
			newvalue.emails = $scope.tvshow.emails;
			this.update(newvalue);
		};

		this.pushTorrent = function() {
			var file = $scope.tvshow.myFile;
			var uploadUrl = '/tvshowlist/pushTorrent';
			fileUpload.uploadFileToUrl(parseInt($scope.tvshow.seriesid),file, uploadUrl);
			$("input[type='file']").val(null);
			$(".uploadFilename").val("");
			$scope.tvshow.myFile = null;
		};

		this.update = function(newvalue) {
			$http({
				method: 'POST',
				url: '/tvshowlist/update',
				data: $.param(newvalue),
				headers: {'Content-Type': 'application/x-www-form-urlencoded'}
			})
			.then(function(data) {
			  	if (data.data.status == 200)
			  		$('#notification').scope().alert_success(data.data);
			  	else
			  		$('#notification').scope().alert_error(data.data);

			});
		};
		this.forceUpdate = function() {
			$http({
				method: 'POST',
				url: '/tvshowlist/update',
				data: $.param({tvShowID:parseInt($scope.tvshow.seriesid),force:true}),
				headers: {'Content-Type': 'application/x-www-form-urlencoded'}
			})
			.then(function(data) {
			  	if (data.data.status == 200)
			  		$('#notification').scope().alert_success(data.data);
			  	else
			  		$('#notification').scope().alert_error(data.data);

			});
		};
	}]);

	app.controller('EpisodeController', [ '$http', '$scope', function($http,$scope){
		this.updateEpisode = function() {
			if (this.form.$valid) {
				$scope.tvShowCtrl.updateEpisode();
				this.form.$setPristine();
			}
		};
	}]);

	app.controller('PatternController', [ '$http', '$scope', function($http,$scope){
		this.updatePattern= function () {
			if (this.form.$valid) {
				$scope.tvShowCtrl.updatePattern();
				this.form.$setPristine();
			}
		};
	}]);

	app.controller('EmailsController', [ '$http', '$scope', function($http,$scope){
		this.addEmail= function () {
			if (this.form.$valid) {
				$scope.tvShowCtrl.addEmail();
				this.form.$setPristine();
			}
		};

		this.deleteEmail = function(email) {
			$scope.tvShowCtrl.deleteEmail(email);
		};
	}]);

	app.controller('KeywordsController', [ '$http', '$scope', function($http,$scope){
		this.addKeyword= function () {
			if (this.form.$valid) {
				$scope.tvShowCtrl.addKeyword();
				this.form.$setPristine();
			}
		};

		this.deleteKeyword = function(keyword) {
			$scope.tvShowCtrl.deleteKeyword(keyword);
		};
	}]);

	app.controller('PushTorrentController', [ '$http', '$scope', function($http,$scope){
		this.uploadFile = function(){
			if (this.form.$valid){
				$scope.tvShowCtrl.pushTorrent();
				this.form.$setPristine();
			}
		};
	}]);

    app.filter('numberFixedLen', function () {
        return function (n, len) {
            var num = parseInt(n, 10);
            len = parseInt(len, 10);
            if (isNaN(num) || isNaN(len)) {
                return n;
            }
            num = ''+num;
            while (num.length < len) {
                num = '0'+num;
            }
            return num;
        };
    });

	app.filter('statusLabel', function() {
		return function (status) {
			return TSWstatus[parseInt(status)];
		}
	});

    app.directive('pattern',function(){
    	return {
    		restrict: 'E',
    		scope: {
    			tvshow: '=',
    			tvShowCtrl: '=tvshowctrl'
    		},
    		controller:'PatternController',
    		controllerAs:'PatternCtrl',
    		templateUrl: 'pattern.html'
    	};
    });

    app.directive('episode',function(){
    	return {
    		restrict: 'E',
    		scope: {
    			tvshow: '=',
    			tvShowCtrl: '=tvshowctrl'
    		},
    		controller:'EpisodeController',
    		controllerAs:'EpisodeCtrl',
    		templateUrl: 'episode.html'
    	};
    });

    app.directive('emails',function(){
    	return {
    		restrict: 'E',
    		scope: {
    			tvshow: '=',
    			tvShowCtrl: '=tvshowctrl'
    		},
    		controller:'EmailsController',
    		controllerAs:'EmailsCtrl',
    		templateUrl: 'emails.html'
    	};
    });

    app.directive('keywords',function(){
    	return {
    		restrict: 'E',
    		scope: {
    			tvshow: '=',
    			tvShowCtrl: '=tvshowctrl'
    		},
    		controller:'KeywordsController',
    		controllerAs:'KeywordsCtrl',
    		templateUrl: 'keywords.html'
    	};
    });

    app.directive('pushTorrent',function(){
    	return {
    		restrict: 'E',
    		scope: {
    			tvshow: '=',
    			tvShowCtrl: '=tvshowctrl'
    		},
    		controller:'PushTorrentController',
    		controllerAs:'PushTorrentCtrl',
    		templateUrl: 'pushTorrent.html'
    	};
    });

    app.directive('fileModel', ['$parse', function ($parse) {
		return {
		    restrict: 'A',
		    link: function(scope, element, attrs) {
		        var model = $parse(attrs.fileModel);
		        var modelSetter = model.assign;

		        element.bind('change', function(){
		            scope.$apply(function(){
		                modelSetter(scope, element[0].files[0]);
		            });
		        });
		    }
		};
	}]);

	/*app.directive('validFile',function(){
	  return {
		require:'fileModel',
		link:function(scope,el,attrs,ngModel){
		  //change event is fired when file is selected
		  el.bind('change',function(){
		    scope.$apply(function(){
		      ngModel.$setViewValue(el.val());
		      ngModel.$render();
		    });
		  });
		}
	  }
	});*/

    app.service('fileUpload', ['$http', function ($http) {
		this.uploadFileToUrl = function(tvshowid, file, uploadUrl){
		    var fd = new FormData();
		    fd.append('torrentFile', file);
		    fd.append('tvShowID', tvshowid);
		    $http.post(uploadUrl, fd, {
		        transformRequest: angular.identity,
		        headers: {'Content-Type': undefined}
		    })
		    .then(function(data){
			  	if (data.data.status == 200)
			  		$('#notification').scope().alert_success(data.data);
			  	else
			  		$('#notification').scope().alert_error(data.data);
		    })
		};
	}]);

    TSWstatus = {
		0: "Added",
		10: "Not yet aired",
		20: "torrent required",
		21: "Waiting torrent push from user",
		22: "Looking for torrent from torrent provider",
		30: "Download in progress",
		35: "Download achieved. To be transfered",
		39: "Download completed",
		90: "Tv Show achieved",
		99: "Error"
	};
})();
