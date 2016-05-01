(function(){
	var app = angular.module('appTsw.TvShow', [ 'ngAnimate', 'ui.bootstrap' ]);
		
	app.controller('TvShowListController', [ '$http', '$scope', function($http,$scope){
		$scope.oneAtATime = true;
		
		var serie_time = "0";
		var tvshowlist = this;
		this.list = [];
		this.source1 = {};
		
		this.check_progression = function(event){
			var tvshow = $.grep(tvshowlist.list, function(e){ return e.seriesid == seriesid; })[0];
			tvshow.progress = event.data;
		};
		var check_progression = this.check_progression;
		
		this.build_tvShowList = function() {
			tvshowlist.list = [];
			$http.get('/tvshowlist/list')
				.success(function(data) {
					tvshowlist.list = data.data;
					for (var i = 0 ; i< tvshowlist.list.length ; i++)
					{
						if ([30,35].indexOf(tvshowlist.list[i]['status']) != -1)
						{
							seriesid = tvshowlist.list[i]['seriesid'];
							this.source1 = new EventSource("/tvshowlist/progression?tvShowID="+seriesid.toString());
							this.source1.onmessage = function(event){
								var tvshow = $.grep(tvshowlist.list, function(e){ return e.seriesid == seriesid; })[0];
								tvshow.progress = event.data;
							};
						}
					}
				});
		};
		build_tvShowList = this.build_tvShowList;
		this.build_tvShowList();
		
		this.tvShowChanged = function(newTvShow){
			for (var i = 0 ; i < tvshowlist.list.length ; i++) {
				if (tvshowlist.list[i].seriesid == newTvShow.seriesid){
					if (!(tvshowlist.list[i].season == newTvShow.season &&
							tvshowlist.list[i].episode == newTvShow.episode &&
							tvshowlist.list[i].pattern == newTvShow.pattern)){
						tvshowlist.list[i] = newTvShow;
					}
				}
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
		
		this.check_update = function(event){
			if ( serie_time == "0" )
			{
				serie_time = event.data;
			}
			if (serie_time != event.data)
			{
				serie_time = event.data;
				update_tvShowList();
			}
		};
		this.source = new EventSource("streamGetSeries");
		this.source.onmessage = this.check_update;
		
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
		
		this.updateEpisode = function(seriesid) {
			var newvalue = {};
			newvalue = {tvShowID:parseInt(seriesid)};
			var tvshow = $.grep(tvshowlist.list, function(e){ return e.seriesid == seriesid; })[0];
			newvalue.season = parseInt(tvshow.season);
			newvalue.episode = parseInt(tvshow.episode);
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
		
		this.updatePattern = function(seriesid) {
			var newvalue = {};
			newvalue = {tvShowID:parseInt(seriesid)};
			var tvshow = $.grep(tvshowlist.list, function(e){ return e.seriesid == seriesid; })[0];
			newvalue.pattern = tvshow.pattern;
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
	}]);
	
	app.controller('NewTvShowController', [ '$http', '$scope',function($http,$scope){
		this.addTvShow = function(tvShowList) {
			this.tvshow.season = 0;
			this.tvshow.episode = 0;
			var index = tvShowList.push(this.tvshow);
			tvShowList[index-1]['isDisable'] = true;
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
