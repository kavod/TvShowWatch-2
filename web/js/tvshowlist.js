(function(){
	var app = angular.module('appTsw.TvShowList', [ 'ngAnimate', 'ui.bootstrap', 'appTsw.TvShow' ]);

		app.run(function($rootScope, $templateCache) {
		   $rootScope.$on('$viewContentLoaded', function() {
			  $templateCache.removeAll();
		   });
		});

	app.controller('TvShowListController', [ '$http', '$scope', 'fileUpload',function($http,$scope,fileUpload){
		$scope.oneAtATime = true;

		var serie_time = "0";
		var tvshowlist = this;
		this.list = [];
		this.source1 = {};

		this.build_tvShowList = function() {
			tvshowlist.list = [];
			$http.get('/tvshowlist/list')
				.success(function(data) {
					tvshowlist.list = data.data;
				});
		};
		build_tvShowList = this.build_tvShowList;
		this.build_tvShowList();

		this.tvShowChanged = function(newTvShow){
			var found = false;
			for (var i = 0 ; i < tvshowlist.list.length ; i++) {
				if (tvshowlist.list[i].seriesid == newTvShow.seriesid){
					for(var prop in newTvShow) { tvshowlist.list[i][prop] = newTvShow[prop];}
					found = true;
					break;
				}
			}
			if (!found) {
				tvshowlist.list.push(newTvShow);
			}
		}
		tvShowChanged = this.tvShowChanged;

		this.update_tvShowList = function(){
			$http.get('/tvshowlist/list')
				.success(function(data) {
					for (var i = 0; i<data.data.length ; i++)
					{
						tvShowChanged(data.data[i]);
					}
				});
		};
		update_tvShowList = this.update_tvShowList;

		this.update_home = function(){
			$('#lastdownloads').scope().updateLog();
		}
		update_home = this.update_home;

		this.check_update = function(event){
			if (event.lastEventId == 'server-time')
			{
				if ( serie_time == "0" )
				{
					serie_time = event.data;
				}
				if (serie_time != event.data)
				{
					console.log([serie_time,event.data])
					serie_time = event.data;
					update_tvShowList();
					update_home();
				}
			} else if (event.lastEventId == 'progression') {
				var data = JSON.parse(event.data);
				for (seriesid in data)
				{
					var tvshow = $.grep(tvshowlist.list, function(e){ return e.seriesid == parseInt(seriesid); })[0];
					if (tvshow === undefined) {
						console.log("Error assigning progress");
						console.log(tvshowlist.list);
						console.log(parseInt(seriesid));
					} else {
						tvshow.progress = data[seriesid];
					}
				}
			} else if (event.lastEventId == 'conf-test') {
				$('#' + event.data).scope().updateConfTest(isOpen=true);
			}
		};
		this.source = new EventSource("streamGetSeries");
		this.source.addEventListener("message",this.check_update);

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
		this.forceUpdate = function() {
			$http({
				method: 'POST',
				url: '/tvshowlist/forceUpdate',
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

	app.controller('NewTvShowController', [ '$http', '$scope',function($http,$scope){
		this.addTvShow = function(tvShowList) {
			console.log($scope);
			if (this.form.$valid) {
					this.tvshow.season = 0;
					this.tvshow.episode = 0;
					console.log(this.tvshow);
					var index = tvShowList.push(this.tvshow);
					tvShowList[index-1]['isDisable'] = true;
					if (typeof(this.tvshow)== 'string')
						this.tvshow = {"title":this.tvshow,"season":0,"episode":0};
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
							$('#notification').scope().alert_success(data);
						} else {
							tvShowList.splice(index-1,1);
							$('#notification').scope().alert_error(data);
						}
					});
					this.form.$setPristine();
			}
		};
	}]);

    app.directive('tvshow',function(){
    	return {
    		restrict: 'E',
    		scope: {
    			tvshow: '=',
    			tvshowlist: '='
    		},
    		controller:'TvShowController',
    		controllerAs:'tvShowCtrl',
    		templateUrl: 'tvShowListElement.html'
    	};
    });
})();
