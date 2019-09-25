/**
 * Función para agregar una fila a la tabla
 * @param table_id Recibe el identificador de la tabla
*/
function appendRow(table_id){
	var html = '<tr><td><input type="text" name="codigo"></td>'
	html += '<td><input type="text" name="nombre"></td>'
	html += '<td><input type="number" name="cantidad" id="cantidad" oninput="changeTotal(this,\''+table_id+'\')"></td>'
	html += '<td><input type="number" name="precio" oninput="changeTotal(this,\''+table_id+'\')" id="precio" step="0.01"></td>'
	html += '<td><input type="text" name="total" readonly="readonly" id="total"></td>'
	html += '<td><a class="btn btn-danger" onclick="remove_row(this,\''+table_id+'\')"> <i class="fa fa-minus" aria-hidden="true"></i></a></td></tr>'
	$(table_id+' tbody').append(html)
}

/**
 * Función para remover una fila
 * @param element Recibe la fila a remover
 * @param table_id Recibe el identificador de la tabla
*/
function remove_row(element, table_id){
	$(element).parent().parent().remove()
	generalTotal(table_id)
}

/**
 * Función para actualizar el total de la tabla
 * @param element Recibe el elemento de la tabla
 * @param table_id Recibe el identificador de la tabla
*/
function changeTotal(element, table_id){
	var parent = $(element).parent().parent()
	var cantidad = parent.find('#cantidad')[0].value
	var precio = parent.find('#precio')[0].value
	if(cantidad && precio){
		var total = parent.find('#total')[0]
		total.value = precio * cantidad
		generalTotal(table_id)
	}
}

/**
 * Función para generar totales en la sección final
 * @param table_id Recibe el identificador de la tabla
*/
function generalTotal(table_id){
	var totales = 0
	$.each($(table_id+' #total'),function(key,value){
		totales += parseFloat(value.value)
	})
	var neto = totales - (totales * (impuesto/100) )
	$('#out_neto').val(neto)
	$('#out_total').val(totales)
}