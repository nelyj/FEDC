function perfil_modals(){
  ruta_user = ruta;
  
    $.ajax({
    url: ruta_user,
    type: "GET",
    data: {
    },
    dataType: 'html',
    success: function(data) {
      $('#modal-body').html(data);
    }
  });
}

function modal_user(id_user){
  ruta_user = ruta.split("/")[1]
  ruta_user = "/"+ruta_user + "/" + id_user + "/"
  $.ajax({
    url: ruta_user,
    type: "GET",
    data: {
    },
    dataType: 'html',
    success: function(data) {
      $('#modal-body').html(data);
    }
  });

}
  $("#perfil").click(function(){
    perfil_modals();
  })


function modal_inbox(id_intercambio){
  $("#myModalLabel").text("Detalles del mensaje")
  ruta_mensaje = ruta_mensaje.split("/", 3)
  ruta_mensaje = ruta_mensaje.join("/") + "/" + id_intercambio
  $.ajax({
    url: ruta_mensaje,
    type: "GET",
    data: {
    },
    dataType: 'html',
    success: function(data) {
      $('#modal-body').html(data);
    }
  });
  
}

function modal_detalle_libro(id_libro){
  $("#myModalLabel").text("Detalles del libro")
  ruta_detail_libro = ruta_detail_libro.split("/", 3)
  ruta_detail_libro = ruta_detail_libro.join("/") + "/" + id_libro
  $.ajax({
    url: ruta_detail_libro,
    type: "GET",
    data: {
    },
    dataType: 'html',
    success: function(data) {
      $('#modal-body').html(data);
    }
  });
}

function eliminar_dte(url){
  $("#myModalLabel").text("Eliminar")
  $.ajax({
    url: url,
    type: "GET",
    data: {
    },
    dataType: 'html',
    success: function(data) {
      $('#modal-body').html(data);
      $('#form_delete').attr('action',url)
    }
  });
}