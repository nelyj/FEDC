/**
 * Función para agregar una fila a la tabla
 * @param table_id Recibe el identificador de la tabla
*/
function appendRow(table_id, product={codigo:'', nombre:'', cantidad:'', precio:'',exento:false}){
	var html = '<tr><td><input type="text" name="codigo" value="'+product.codigo+'"></td>'
	html += '<td><input type="text" name="nombre" value="'+product.nombre+'"></td>'
	html += '<td><input type="number" name="cantidad" id="cantidad" oninput="changeTotal(this,\''+table_id+'\')" value="'+product.cantidad+'"></td>'
	html += '<td><input type="number" name="precio" oninput="changeTotal(this,\''+table_id+'\')" id="precio" step="0.01" value="'+product.precio+'"></td>'
	html += '<td><input type="number" name="descuento" oninput="changeTotal(this,\''+table_id+'\')" id="descuento" value="'+product.descuento+'"></td>'
	html += '<td><select name="exento" onchange="changeTotal(this,\''+table_id+'\')" id="exento">'
	html += '<option value="0">No</option><option value="1">Si</option></select></td>'
	html += '<td><input type="text" name="total" readonly="readonly" id="total" value="'+product.cantidad*product.precio+'"></td>'
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
	var descuento = parent.find('#descuento')[0].value
	if(cantidad && precio){
		var total = parent.find('#total')[0]
		if(descuento){
			var f_total = precio * cantidad
			total.value = f_total - (f_total*(descuento/100))
		}else{
			total.value = precio * cantidad
		}
		generalTotal(table_id)
	}
}

/**
 * Función para generar totales en la sección final
 * @param table_id Recibe el identificador de la tabla
*/
function generalTotal(table_id){
	var neto = 0
	var exento = 0
	$.each($(table_id+' #total'),function(key,value){
		if($(value).parent().parent().find("#exento")[0].value){
			exento += parseFloat(value.value)
		}else{
			neto += parseFloat(value.value)
		}
	})
	var total = (neto + (neto * (impuesto/100) )) + exento
	$('#out_neto').val(neto)
	$('#out_total').val(total)
	$('#out_exento').val(exento)
}
