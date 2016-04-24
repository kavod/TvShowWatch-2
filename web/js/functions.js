var serie_time = "0";

function compare(a,b) {
	if (a.title < b.title)
		return -1;
	else if (a.title > b.title)
		return 1;
	else 
		return 0;
}

function format_episode(season,episode) {
	season = season.toString()
	episode = episode.toString()
	season = (parseInt(season) > 9) ? season : "0"+season;
	episode = (parseInt(episode) > 9) ? episode : "0"+episode;
	return "S" + season + "E" + episode;
}

function alert_error(except) {
	new PNotify({
		title: 'Error',
		text: except.error,
		type: 'error'
	});
}

function alert_success(except) {
	new PNotify({
		title: 'Success',
		text: except.error,
		type: 'success'
	});
}

function tvShowList_add(searchField) {
	$.ajax({
	  type: "POST",
	  url: "tvshowlist/add",
	  data: { "search": searchField.getValue() },
	  
	})
	.done(function(data) {
	  	if (data.status == 200) {
	  		searchField.setValue("");
	  		alert_success(data);
	  		//build_tvShowList();
	  	} else {
	  		alert_error(data);
	  	}
	  });
}

TSWstatus = {
	0: "Added",
	10: "Not yet aired",
	20: "Watching torrent",
	30: "Download in progress",
	35: "Download achieved. To be transfered",
	90: "Tv Show achieved",
	99: "Error"
}

function statusLabel(status) {
	return TSWstatus[parseInt(status)];
}

function build_tvShowList() {
	/*console.log("build_tvShowList");
	$.ajax({
	  type: "GET",
	  url: "/data/tvShowList/",
	  accept: "application/json"
	})
		.done(function(data) {
			console.log(data);
			//result = JSON.parse(data);
			$("#accordion").html("");
			data.sort(compare);
			for (serie in data)
			{
				if (typeof data[serie].info === 'undefined')
					data[serie].info = {}
				if (data[serie].info.banner_url === 'undefined') {
					bannerNode = $('<div>')
				} else {
					bannerNode = $('<img>').attr('src',data[serie].info.banner_url)
				}
				
				formatedEpisode = format_episode(data[serie].season,data[serie].episode)
				
				var d = new Date(data[serie].info.firstaired);
				dateString = d.getDate() + '/' + d.getMonth() + '/' + d.getFullYear();
				nextBroadcast = "Broadcast date of " + formatedEpisode + ": " + dateString;
				
				$("#accordion").append($("<div>")
					.addClass("panel")
					.addClass("panel-default")
					.addClass("TvShowList")
					.attr("seriesid",data[serie].seriesid)
					.append($("<div>")
						.addClass("panel-heading")
						.append($("<div>")
							.addClass("tvShowTitle")
							.append($("<a>")
								.attr("data-target","#tvShow" + data[serie].seriesid)
								.attr("data-toggle","collapse")
								.attr("aria-expanded",true)
								.attr("aria-controls","tvShow" + data[serie].seriesid)
								.attr("data-parent","#accordion")
								.text(data[serie].title)
							)
						)
						.append($("<div>")
							.addClass("tvShowEpisode")
							.text(formatedEpisode)
						)
						.append($("<div>")
							.addClass("tvShowStatus")
							.text(statusLabel(data[serie].status))
						)
						.append($("<button>")
							.addClass("btn btn-default")
							.attr("aria-label","Delete")
							.addClass("right_float")
							.append($("<span>")
								.addClass("glyphicon")
								.addClass("glyphicon-trash")
								.attr("aria-hidden",true)
							)
							.click(function() {
								$.ajax({
								  type: "POST",
								  url: "tvshowlist/delete",
								  data: { "tvShowID": parseInt(this.parentNode.parentNode.getAttribute("seriesid")) },
								  
								})
									.done(function(data) {
									  	if (data.status == 200) {
									  		alert_success(data);
									  		build_tvShowList();
									  	} else {
									  		alert_error(data);
									  	}
									  });
							})
						)
					)
					.append($("<div>")
						.addClass("collapse")
						.attr("id","tvShow" + data[serie].seriesid)
						.append($('<h3>')
							.text(data[serie].title)
						)
						.append(bannerNode)
						.append($("<p>")
							.text(data[serie].info.overview)
						)
						.append($("<p>")
							.text(nextBroadcast)
						)
					)
				);
			}
		}
	);*/
}

function check_update(event)
{
	if (serie_time == "0")
	{
		initial_update = true;
	}
	if (serie_time != event.data)
	{
		serie_time = event.data;
		//build_tvShowList();
	}
}
