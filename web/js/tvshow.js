(function(){
	var app = angular.module('appTsw.TvShow', [ 'ngAnimate', 'ui.bootstrap' ]);
	
	app.controller('TvShowListController', [ '$http', '$scope', function($http,$scope){
		$scope.oneAtATime = true;
		
		var tvshowlist = this;
		tvshowlist.list = [];
		$http.get('/data/tvShowList')
			.success(function(data) {
				tvshowlist.list = data;
			});
			
		this.delete = function(seriesid) {
			$http({
				method: 'POST',
				url: '/tvshowlist/delete',
				data: $.param({ "tvShowID": seriesid }),
				headers: {'Content-Type': 'application/x-www-form-urlencoded'}
			})
			.then(function(data) {
			  	if (data.data.status == 200)
			  		$('#notification').scope().alert_success(data.data);
			  	else
			  		$('#notification').scope().alert_error(data.data);
				
			});
			var seriesidx = $.grep(tvshowlist.list, function(e){ return e.seriesid == seriesid; });
			//seriesidx = tvshowlist.list.indexOf(seriesid);
			if (seriesidx.length == 0) {
				$('#notification').scope().alert_error({"status":400,"error":"Unable to find the TV Show (" + seriesid.toString() + ")"});
			} else {
				tvshowlist.list.forEach(function(item, index, object) {
				  if (item.seriesid === seriesid) {
					object.splice(index, 1);
				  }
				});
			}
		};
	}]);
	
	app.controller('NewTvShowController', [ '$http', '$scope',function($http,$scope){
		//this.tvshow = {'value':''};
		this.addTvShow = function(tvShowList) {
			this.tvshow.season = 0;
			this.tvshow.episode = 0;
			var index = tvShowList.push(this.tvshow);
			tvShowList[index-1]['isDisable'] = true;
			//this.tvshow = {'value':''};
			var postData = $.param(this.tvshow);
			delete this.tvshow;
			$http({
				method: 'POST',
				url: '/tvshowlist/add',
				data: postData,
				headers: {'Content-Type': 'application/x-www-form-urlencoded'}
			})
			.success(function(data) {
				if (data['status'] == 200)
				{
					tvShowList[index-1] = data['data'];
					//$scope.$apply();
					$('#notification').scope().alert_success(data);
				} else {
					tvShowList.splice(index-1,1);
					$('#notification').scope().alert_error(data);
				}
			});
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
    
    app.directive('tvshow',function(){
    	return {
    		restrict: 'E',
    		scope: {
    			tvshow: '=',
    			tvshowlist: '='
    		},
    		templateUrl: 'tvShowListElement.html'
    	};
    });
    
    TSWstatus = {
		0: "Added",
		10: "Not yet aired",
		20: "Watching torrent",
		30: "Download in progress",
		35: "Download achieved. To be transfered",
		90: "Tv Show achieved",
		99: "Error"
	};
})();
