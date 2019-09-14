function appendRow(table_id){
	//var elements = $(table_id+' tbody tr').length + 1
	var html = '<tr><td><input type="text" name="codigo"></td>'
	html += '<td><input type="text" name="nombre"></td>'
	html += '<td><input type="number" name="cantidad"></td>'
	html += '<td><input type="number" name="precio"></td>'
	html += '<td><input type="text" name="total" readonly="readonly"></td>'
	html += '<td><a class="btn btn-danger" onclick="remove_row(this)"> <i class="fa fa-minus" aria-hidden="true"></i></a></td></tr>'
	$(table_id+' tbody').append(html)
}

function remove_row(element){
	$(element).parent().parent().remove()
}