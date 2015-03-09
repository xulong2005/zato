
$.fn.zato.process.definition.on_validate_save = function(e) {
    $.fn.zato.user_message(e.statusText == 'OK', e.responseText);
}

$.fn.zato.process.definition._validate_save = function(e, extra) {
    var form = $("#process-definition-validate-save");
    var data = form.serialize();
    data += String.format("&{0}=1", extra);
    e.preventDefault();
    $.fn.zato.post(form.attr('action'), $.fn.zato.process.definition.on_validate_save, data);
    return false;
}

$.fn.zato.process.definition.validate = function(e) {
    $.fn.zato.process.definition._validate_save(e, 'validate');
}

$.fn.zato.process.definition.validate_save = function(e) {
    $.fn.zato.process.definition._validate_save(e, 'validate_save');
}

$(document).ready(function() { 
    $("#validate").click($.fn.zato.process.definition.validate);
    $("#validate_save").click($.fn.zato.process.definition.validate_save);
})
