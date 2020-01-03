
$(document).ready(function() {
    $("#id_is_staff").on("change", function(){
        if ($('#id_is_staff').is(':checked')){
            $.each([1], function(i,e){
                $("#id_groups option[value='" + e + "']").prop("selected", true);
            });
        }
        else{
            $.each([1], function(i,e){
                $("#id_groups option[value='" + e + "']").prop("selected", false);
            });   
        }
    });
    
    $('#show').click(function(){
        $('#show').removeClass( "glyphicon glyphicon-eye-open" ).addClass( "glyphicon glyphicon-eye-close" )
        if (!$("#check").is(':checked')){
                $("#check").prop("checked", true)
                $("#check").attr('checked', 'checked')
                $("#check").is(':checked') ? $('#id_password1').attr('type', 'text') : $('#id_password1').attr('type', 'password');
        }
        else{
            $('#show').removeClass( "glyphicon glyphicon-eye-close" ).addClass( "glyphicon glyphicon-eye-open" )
            $("#check").prop("checked", false)
            $("#check").is(':checked') ? $('#id_password1').attr('type', 'text') : $('#id_password1').attr('type', 'password');
        }
    });

    $('#meter').entropizer({
        target: '#id_password1',
        update: function(data, ui) {
            ui.bar.css({
                'background-color': data.color,
                'width': data.percent + '%'
            });
        }
    });
});

function ramdomString(length){
        var password = Math.random().toString(36).substring(2, length) + Math.random().toString(36).substring(2, length);
        $('#id_password1').val(password)
        $('#id_password2').val(password)
        $('#meter').entropizer('destroy');
        $('#meter').entropizer({
            target: '#id_password1',
            update: function(data, ui) {
                ui.bar.css({
                    'background-color': data.color,
                    'width': data.percent + '%'
                });
            }
        });
        return password;
};
