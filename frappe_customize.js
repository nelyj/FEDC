frappe.ui.form.on('Sales Invoice', {
	refresh: function(frm) {
		var estado =(frm.doc.__islocal ? 0 : 1)
		if(estado==1){
			var data= {"data": frm.doc}
			var url="http://localhost:8080/api/facturas/1/"+frm.doc.name+"/"
			var settings = {
				"async": true,
				"url": url,
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
	}
})

frappe.ui.form.on('Sales Invoice', {
	refresh: function(frm) {
		var estado =(frm.doc.__islocal ? 0 : 1)
		if(estado==1){
			var data= {"data": frm.doc}
			var url="http://localhost:8080/api/facturas/"+frm.doc.company+"/"+frm.doc.name+"/"
			var settings = {
				"async": true,
				"url": url,
				"method": "POST",
				"dataType": 'json',
				"contentType": 'application/json',
				"headers": {
					"authorization": "Token 7ee81f6e8b7e15555043a9af5262639cb282946d",
				},
				"data": JSON.stringify(data)
			}
			$.ajax(settings).done(function (response) {
				validated=true;
				msgprint('Envio exitoso');
			});
			$.ajax(settings).fail(function (response) {
				validated=false;
				msgprint('No se puedo enviar al SII');
			});
		}
	}
})