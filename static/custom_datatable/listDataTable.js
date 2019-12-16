$(document).ready(function() {
   data_table = $('#datatable').DataTable({
        "processing": true,
        "serverSide": true,
        "destroy": true,
        "ajax": URL,
        language: {
            url: JSON_DATA
        }
    });
});