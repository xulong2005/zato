
$.fn.zato.process.definition.on_validate = function(e) {
    $.fn.zato.user_message(e.statusText == 'OK', e.responseText);
}

$.fn.zato.process.definition.on_validate_save = function(e) {
    if(e.statusText == 'OK') {
        window.location.replace(e.responseText)
    }
    else {
        $.fn.zato.user_message(false, e.responseText);
    }
}

$.fn.zato.process.definition.on_highlight = function(e) {
    if(e.statusText != 'OK') {
        $.fn.zato.user_message(false, e.responseText);
    }

    var highlight = e.responseText;
    var ta = $('#id_text');

    if($.fn.zato.process.definition.current_state == 'textarea') {
        ta.fadeOut(70, function() {
            $('#text_cell').append(highlight);
            $.fn.zato.process.definition.current_state = 'highlight';
        });
    }
    else {
        $.fn.zato.process.definition.current_state = 'textarea';
        $('.highlighttable').remove();
        ta.fadeIn(70);
    }
}

$.fn.zato.process.definition._on_click = function(e, extra, callback, suppress_user_message) {
    var form = $("#process-definition");
    var data = form.serialize();
    data += String.format("&action={0}", extra);
    e.preventDefault();
    $.fn.zato.post(form.attr('action'), callback, data, 'json', suppress_user_message);
    return false;
}

$.fn.zato.process.definition.toggle_highlight = function(e) {
    $.fn.zato.process.definition._on_click(e, 'toggle_highlight', $.fn.zato.process.definition.on_highlight, true);
}

$.fn.zato.process.definition.validate = function(e) {
    if($('#process-definition').data('bValidator').validate()) {
        $.fn.zato.process.definition._on_click(e, 'validate', $.fn.zato.process.definition.on_validate_save, false);
    }
}

$.fn.zato.process.definition.validate_save = function(e) {
    if($('#process-definition').data('bValidator').validate()) {
        $.fn.zato.process.definition._on_click(e, 'validate_save', $.fn.zato.process.definition.on_validate_save, false);
    }
}

$(document).ready(function() { 

    $.fn.zato.process.definition.current_state = 'textarea';

    $("#toggle_highlight").click($.fn.zato.process.definition.toggle_highlight);
    $("#validate").click($.fn.zato.process.definition.validate);
    $("#validate_save").click($.fn.zato.process.definition.validate_save);

    $.each(['name', 'text'], function(ignored, name) {
        $.fn.zato.data_table.set_field_required('#id_' + name);
    })
    $('#process-definition').bValidator();

})
