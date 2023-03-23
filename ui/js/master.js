var wss = false;
var sid = false;
var output = [];
var active_console = '';

function test() {
    api_request('test')
}

function wss_connect(port) {
    const url = new URL(window.location.href);
    wss = new WebSocket('ws://'+url.hostname+':'+port);

    wss.onmessage = (event) => {
        data = JSON.parse(event.data);
        method = data.M;
        payload = data.D;
        if (method == 'APPRUN') {
            $('#apprunning_'+payload).html("True");
        }
        if (method == 'APPSTOP') {
            $('#apprunning_'+payload).html("False");
        }
        if (method == 'CONSOLE') {
            if (!(payload.R in output)) {
                output[payload.R] = [];
            }
            output[payload.R].push(payload.M);
        }
    };    
    wss.onopen = (event) => {
        wss_send("AUTH", sid);
    };    
}

function wss_send(method, data) {
    var s = {
        'M': method,
        'D': data
    }
    wss.send(JSON.stringify(s))
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

