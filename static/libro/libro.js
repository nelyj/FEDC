$(document).ready(function() {
    var today = new Date()

    $("#id_current_date").datepicker({
        format: "dd/mm/yyyy",
        startDate: 'month',
        endDate: "31/12/"+ today.getFullYear(),
        changeYear: false,
        autoclose: true,
        viewMode: "months", 
        minViewMode: "months"
    })
})

function enviar_libro(pk){
   $.ajax({
      url: '/libro/enviar/'+pk,
      type: "POST",
      data: {
      },
      success: function(data) {
      	location.reload(true);
      }
  });
}
