/**
 * Función para agregar una fila a la tabla
 * @param table_id Recibe el identificador de la tabla
*/
function appendRow(table_id, product={codigo:'', nombre:'', cantidad:'', precio:'',exento:0, descuento:''}){
	var html = '<tr><td><input type="text" name="codigo" value="'+product.codigo+'"></td>'
	html += '<td><input type="text" name="nombre" value="'+product.nombre+'"></td>'
	html += '<td><input type="number" name="cantidad" id="cantidad" oninput="changeTotal(this,\''+table_id+'\')" value="'+product.cantidad+'"></td>'
	html += '<td><input type="number" name="precio" oninput="changeTotal(this,\''+table_id+'\')" id="precio" step="0.01" value="'+product.precio+'"></td>'
	html += '<td><input type="number" name="descuento" oninput="changeTotal(this,\''+table_id+'\')" id="descuento" value="'+product.descuento+'"></td>'
	html += '<td><select name="exento" onchange="changeTotal(this,\''+table_id+'\')" id="exento">'
	if (product.exento == 1)
		html += '<option value="0">No</option><option value="1" selected>Si</option>'
	else
		html += '<option value="0" selected>No</option><option value="1">Si</option>'
	html += '</select></td>'
	if (product.descuento != ''){
		var f_total = product.cantidad * product.precio;
		html += '<td><input type="text" name="total" readonly="readonly" id="total" value="'+(f_total-(f_total*(product.descuento/100)))+'"></td>'
		console.log(html)
	}
	else{
		html += '<td><input type="text" name="total" readonly="readonly" id="total" value="'+product.cantidad*product.precio+'"></td>'
	}
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
		if($(value).parent().parent().find("#exento")[0].value==1){
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

/**
 * Función para mostrar los campos requeridos de nota
 * crédito y débito
 * @param select_value Recibe el valor del id
*/
function show_dte_fields(select_value){
	var val = $(select_value).val()
	if(val == 56 || val == 61){
		$('#dte_hidden').show()
		disable_dte_table_buttons(true)
	}else{
		$('#dte_hidden').hide()
		disable_dte_table_buttons(false)
	}
}

/**
 * Función para cargar la información del dte
 * @param dte_value Recibe el id del dte
*/
function load_dte_info(dte_value){
	if(dte_value){
		$.ajax({
	    type: 'GET',
	    url: LOAD_DTE.replace(0,dte_value),
	    success: function(response) {
	      if(response.success){
	      	let data = response.data[0]
	      	loadData(data.fields)
	      }else{
	      	alert(response.msg)
	      }
	    }	
	  });
  }
}

/**
 * Función para parsear y modelar la data cargada
 * @param data Recibe el objeto de la data
*/
function loadData(data){
	$('#myTable tbody').html("")
	let keys = Object.keys(data)
	for(let value of keys){
		if(value!='productos' || value!='numero_factura'){
			if(value=='fecha'){
				let new_date = data[value].split('-')
				let new_value = new_date[2]+'/'+new_date[1]+'/'+new_date[0]
				$('#id_'+value).val(new_value)
			}else{
				$('#id_'+value).val(data[value])
			}
			$('#id_'+value).attr('readonly',true)
		}
	}
	let productos = JSON.parse(data['productos'])
	for(let item of productos){
		let new_item = {
			codigo:item.item_code, 
			nombre:item.item_name, 
			cantidad:item.qty, 
			precio:item.base_net_rate,
			exento:item.exento,
			descuento:item.discount
		}
		appendRow('#myTable',new_item)
	}
	ei_table('#myTable',true)
	disable_dte_table_buttons(true)
	generalTotal('#myTable')
	enable_dte_fields($('#id_cod_ref').val())
}

/**
 * Función para colocar en modo lectura o no
 * los input de la tabla
 * @param table_name Recibe el nombre de la tabla
 * @param disable Recibe si el se habilita o no el campo
*/
function ei_table(table_name, disable){
	$.each($(table_name+' tbody input'),function(key,value){
		if($(value).attr('name')!='total'){
			if(disable){
				$(value).attr('readonly',true)
			}
			else{
				$(value).removeAttr('readonly')
			}
		}
	})
}

/**
 * Función para colocar editables algunos
 * campos dependiendo del código de referencia
 * @param value Recibe el valor del código de referencia
*/
function enable_dte_fields(value){
	if(value==1){
		dte_fields(false)
		ei_table('#myTable',true)
	}
	else if(value==2){
		dte_fields(true)
		ei_table('#myTable',true)
	}
	else if(value==3){
		dte_fields(false)
		ei_table('#myTable',false)
	}
}

/**
 * Función para habilitar/deshabilitar
 * campos del dte
 * @param enable Recibe si se activan o no
*/
function dte_fields(enable){
	const fields = ['senores','direccion', 'comuna', 
		'region', 'ciudad_receptora','giro', 'rut', 'fecha', 
		'forma_pago', 'descuento_global', 'glosa_descuento']
	for(let value of fields){
		if(enable){
			$('#id_'+value).removeAttr('readonly')
		}
		else{
			$('#id_'+value).attr('readonly',true)
		}
	}
}

/**
 * Función para habilitar/deshabilitar
 * los botones de la tabla
 * @param disable Recibe si se activan o no
*/
function disable_dte_table_buttons(disable){
	$.each($('.table-responsive a'),function(key,value){
		if(disable){
			$(value).attr('disabled',true)
		}
		else{
			$(value).removeAttr('disabled')
		}
	})
}