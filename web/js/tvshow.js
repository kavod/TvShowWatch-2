(function(){
	var app = angular.module('appTsw.TvShow', [ 'ngAnimate', 'ui.bootstrap' ]);
		
	app.controller('TvShowListController', [ '$http', '$scope', function($http,$scope){
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
				}
			} else {
				var data = JSON.parse(event.data);
				for (seriesid in data)
				{
					var tvshow = $.grep(tvshowlist.list, function(e){ return e.seriesid == parseInt(seriesid); })[0];
					if (tvshow === undefined) {
						console.log("Error assigning progress")
						console.log(tvshowlist.list)
						console.log(parseInt(seriesid))
					} else {
						tvshow.progress = data[seriesid];
					}
				}
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
		
		this.updateEmails = function(seriesid) {
			var newvalue = {};
			newvalue = {tvShowID:parseInt(seriesid)};
			var tvshow = $.grep(tvshowlist.list, function(e){ return e.seriesid == seriesid; })[0];
			tvshow.emails.push(tvshow.newEmail);
			newvalue.emails = tvshow.emails;
			delete(tvshow.newEmail);
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
		
		this.deleteEmail = function(seriesid,email) {
			var newvalue = {};
			newvalue = {tvShowID:parseInt(seriesid)};
			var tvshow = $.grep(tvshowlist.list, function(e){ return e.seriesid == seriesid; })[0];
			var index = tvshow.emails.indexOf(email);
			if (index > -1) {
				tvshow.emails.splice(index, 1);
			}
			newvalue.emails = tvshow.emails;
			console.log(newvalue.emails);
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
		
		this.updateKeywords = function(seriesid) {
			var newvalue = {};
			newvalue = {tvShowID:parseInt(seriesid)};
			var tvshow = $.grep(tvshowlist.list, function(e){ return e.seriesid == seriesid; })[0];
			tvshow.keywords.push(tvshow.newKeyword);
			newvalue.keywords = tvshow.keywords;
			delete(tvshow.newKeyword);
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
		
		this.deleteKeyword = function(seriesid,keyword) {
			var newvalue = {};
			newvalue = {tvShowID:parseInt(seriesid)};
			var tvshow = $.grep(tvshowlist.list, function(e){ return e.seriesid == seriesid; })[0];
			var index = tvshow.keywords.indexOf(keyword);
			if (index > -1) {
				tvshow.keywords.splice(index, 1);
			}
			newvalue.keywords = tvshow.keywords;
			console.log(newvalue.keywords);
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
		
		this.pushTorrent = function(seriesid) {
			var newvalue = {};
			newvalue = {tvShowID:parseInt(seriesid)};
			var tvshow = $.grep(tvshowlist.list, function(e){ return e.seriesid == seriesid; })[0];
			console.log(tvshow.torrentFile)
			newvalue.torrentFile = tvshow.torrentFile;
			console.log(newvalue);
			$http({
				method: 'POST',
				url: '/tvshowlist/pushTorrent',
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
			if (typeof(this.tvshow)== 'string')
				this.tvshow = {"title":this.tvshow};
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
    
    // By Endy Tjahjono from http://stackoverflow.com/questions/17063000/ng-model-for-input-type-file
    app.directive("fileread", [function () {
		return {
		    scope: {
		        fileread: "="
		    },
		    link: function (scope, element, attributes) {
		        element.bind("change", function (changeEvent) {
		            var reader = new FileReader();
		            reader.onload = function (loadEvent) {
		                scope.$apply(function () {
		                    scope.fileread = loadEvent.target.result;
		                });
		            }
		            reader.readAsDataURL(changeEvent.target.files[0]);
		        });
		    }
		}
	}]);
    
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
