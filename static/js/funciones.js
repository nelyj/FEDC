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
