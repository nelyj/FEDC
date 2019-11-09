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

    $("#id_periodo").datepicker({
        format: "dd/mm/yyyy",
        //startDate: 'month',
        endDate: today,
        changeYear: false,
        autoclose: true,
        viewMode: "months", 
        minViewMode: "months"
    })
})

function enviar_libro(element, pk){
  $(".se-pre-con").fadeOut("slow").show();
  $(element).attr("disabled", true);
  $('#mensaje_spinner').text('Se esta enviando el libro al sii, por favor espere...')
   $.ajax({
      url: '/libro/enviar/'+pk,
      type: "POST",
      data: {
      },
      success: function(data) {
      	location.reload(true);
        $(".se-pre-con").fadeOut("slow").hide();
        $(element).attr("disabled", false); 
      }
  });
}
