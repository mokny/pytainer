var wss = false;
var sid = false;

function test() {
    api_request('test')
}

function wss_connect(port) {
    const url = new URL(window.location.href);
    wss = new WebSocket('ws://'+url.hostname+':'+port);

    wss.onmessage = (event) => {
        console.log(event.data);
    };    
    wss.onopen = (event) => {
        console.log(event.data);
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

