/*
 * Función para mostrar o ocultar un campo 
 * @param field Recibe el campo a ocultar
 * @param show Recibe si el campo se debe ocultar o no
*/

function showField(field, show){
  if(show){
    $(field).show()
  }
  else{
    $(field).hide()
  }
}

/*
 * Función para enviar al sii
 * @param url Recibe la url de envío
*/
function send_to_sii(url){
	$.ajax({
    type: 'GET',
    url: url,
    success: function(response) {
      if(response['status']){
      	alert(response['msg'])
      }
      else{
      	console.log(response['msg'])	
      }
    }
  }) 
}
