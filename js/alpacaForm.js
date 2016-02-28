function alpacaForm(id) {
	return {
		"schemaSource": "/schema/" + id + "/",
		"optionsSource":"/options/" + id + "/",
		"dataSource":"/data/" + id + "/",
		"options": {
			"form": {
                "buttons":{
                    "submit":{
                        "title": "Send Form Data",
                        "click": function() {
                            var val = this.getValue();
                            if (this.isValid(true)) {
                                console.log("Valid value: " + JSON.stringify(val, null, "  "));
                                $.ajax({
									url: "update/" + id + "/",
									type: 'POST',
									data: {
										"id":"conf",
										"data":JSON.stringify(val, null, "  "),
									},
									"cache": false,
                                });
                            } else {
                                alert("Invalid value: " + JSON.stringify(val, null, "  "));
                            }
                        }
                    }
                }
			}
		}
	};
};

$(document).ready(function() {
	Alpaca.defaultToolbarSticky = true;
});
