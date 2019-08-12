$(document).ready(function() {
    var today = new Date()

    $("#id_current_date").datepicker({
        format: "dd/mm/yyyy",
        startDate: 'month',
        endDate: "31/12/"+ today.getFullYear(),
        changeYear: false,
        autoclose: true,
    })
})