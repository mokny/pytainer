function test() {
    api_request('test')
}


function api_request(method, payload = false, callback = false) {
    if (!payload) payload = {}

    $.post( '/' + method, payload)
        .done(function( data ) {
            if (callback) {
                callback(JSON.parse(data));
            } else {
                alert(data)
            }
        }
    );    
}

function ajax_load(id, file) {
    $.get(file, function( data ) {
        $('#' + id).html(data);
    });
}
