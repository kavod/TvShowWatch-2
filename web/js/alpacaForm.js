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
                                })
																.done(function(data, textStatus, jqXHR) {
																	console.log(data);
															  	if (data.status == 200)
															  		$('#notification').scope().alert_success(data);
															  	else
															  		$('#notification').scope().alert_error(data);
																});
                            } else {
                                alert("Invalid value: " + JSON.stringify(val, null, "  "));
                            }
                        }
                    }
                }
			}
		},
		"postRender": function(control) {
	    if (control.form) {
	        control.form.registerSubmitHandler(function (e) {
		        control.form.getButtonEl('submit').click();
		        return false;
		    });
			}
		}
	};
};

$(document).ready(function() {
	Alpaca.defaultToolbarSticky = true;
});
