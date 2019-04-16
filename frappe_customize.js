frappe.ui.form.on('Sales Invoice', {
	refresh: function(frm) {
		var data= {"data": frm.doc}
		var settings = {
			"async": true,
			"url": "http://localhost:8000/api/facturas/",
			"method": "POST",
			"dataType": 'json',
			"contentType": 'application/json',
			"headers": {
				"authorization": "Token 7ee81f6e8b7e15555043a9af5262639cb282946d",
			},
			"data": JSON.stringify(data)
		}
		$.ajax(settings).done(function (response) {
			console.log(response);
		});
	}
})