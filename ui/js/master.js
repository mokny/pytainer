var wss = false;
var sid = false;
var output = [];
var active_console = '';
var _active_repo = '';

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
            if (typeof setRunning !== "undefined") { 
                setRunning(payload, true);
            }
            if (typeof setDetailsRunning !== "undefined") { 
                if (payload == _active_repo)
                    setDetailsRunning(true);
            }
        }

        if (method == 'APPSTOP') {
            if (typeof setRunning !== "undefined") { 
                setRunning(payload, false);
            }
            if (typeof setDetailsRunning !== "undefined") { 
                if (payload == _active_repo)
                    setDetailsRunning(false);
            }
        }

        if (method == 'CONSOLE') {
            if (!(payload.R in output)) {
                output[payload.R] = [];
            }
            output[payload.R].push(payload.M);
            if (typeof addCardConsole !== "undefined") { 
                addCardConsole(payload.R, payload.M);
            }            
            if (typeof addDetailedConsole !== "undefined") {
                if (payload.R == _active_repo) {
                    addDetailedConsole(payload.M);
                }
            }            
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
    $('#' + id).html('<div style="text-align:center"><div class="spinner-border" style="width: 3rem; height: 3rem;" role="status"><span class="visually-hidden">Loading...</span></div></div>');
    $.get(file, function( data ) {
        $('#' + id).html(data);
    });
    return false;
}

