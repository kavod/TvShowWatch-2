$(document).ready(function() {
	PNotify.prototype.options.styling = "bootstrap3";
	var serie_time = "0";
		
	$("#test").click(function() {
		alert_error({"status":400,"error":"My bad"});
	})
	$("#tabs").tab();
	$("#tabs-conf").tab();
    $("#torrent-search").alpaca(alpacaForm("torrentSearch"));
    $("#downloader").alpaca(alpacaForm("downloader"));
    $("#transfer").alpaca(alpacaForm("transferer"));
    $("#tvshow").alpaca({
    	"dataSource":"/data/tvShowList/",
		"schemaSource": "/schema/tvShowList/",
		"options":{
			"type":"table",
			"items":{
				"fields":{
					"seriesid":{
						/*"view":"bootstrap-display",*/
						"validate":false
					},
					"status":{
						/*"view":"bootstrap-display",*/
						"validate":false
					},
					"season":{
						/*"view":"bootstrap-display",*/
						"validate":false
					},
					"episode":{
						/*"view":"bootstrap-display",*/
						"validate":false
					},
					"downloader_id": {
						"hidden":true
					}
				},
				/*"legendStyle":"hidden"*/
			},
			"hideInitValidationError":false
		},
		"view":"bootstrap-display"
    });
    
    build_tvShowList();
	
	// constructs the suggestion engine
	var states = new Bloodhound({
	  datumTokenizer: Bloodhound.tokenizers.whitespace,
	  queryTokenizer: Bloodhound.tokenizers.whitespace,
	  // `states` is an array of state names defined in "The Basics"
	  remote : {
	  	url:'/livesearch/%QUERY',
	  	wildcard: '%QUERY'
	  },
	});
	
    $("#search_tvshow").alpaca({
		"schema": {
			"type":"object",
			"properties": {
				"search": {
					"type": "string"
				}
			}
		},
		"options": {
			"fields": {
				"search": {
					"type": "search",
					"placeholder":"Type your favorite TV Show name",
					"events": {
						"keydown": function(e) {
							if (e.keyCode == '13')
							{
								tvShowList_add(this);
							}
						}
					},
					"typeahead" : {
						"config": {
						  hint: true,
						  highlight: true,
						  minLength: 3
						},
						"datasets": {
						  name: 'states',
						  source: states.ttAdapter(),
						  displayKey: 'value',
						  limit: 9,
						  templates: {
						  	"suggestion":function(data) {
						  		return '<p>' + data.value + '<br />'
						  			 + '<small>' + data.info + '</small></p>';
						  	}
						  }
						}
					}
				}
			}
		}
	});
	
	var source = new EventSource("streamGetSeries");
	source.onmessage = check_update;
});
