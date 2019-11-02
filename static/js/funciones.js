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
  $(".se-pre-con").fadeOut("slow").show();
  $("#send_dte").attr("disabled", true);
  $('#mensaje_spinner').text('Se esta enviando el DTE al sii, por favor espere...')
  $.ajax({
    type: 'GET',
    url: url,
    success: function(response) {
      if(response['status']){
        $(".se-pre-con").fadeOut("slow").hide();
        $("#send_dte").attr("disabled", false); 
        alert(response['msg'])
        data_table.ajax.reload( null, true );
      }
      else{
      	console.log(response['msg'])
        $(".se-pre-con").fadeOut("slow").hide();
        $("#send_dte").attr("disabled", false); 
      }
    }
  }) 
}
