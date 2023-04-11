var wss = false;
var sid = false;
var output = [];
var active_console = '';
var _active_repo = '';
var _performance = [];
var _modalinputcallback = false;


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
            if (typeof setEditorRunning !== "undefined") { 
                if (payload == _active_repo)
                    setEditorRunning(true);
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
            if (typeof setEditorRunning !== "undefined") { 
                if (payload == _active_repo)
                    setEditorRunning(false);
            }
        }

        if (method == 'CONSOLE') {
            if (!(payload.R in output)) {
                output[payload.R] = [];
            }

            output[payload.R].push(payload.M);

            if (output[payload.R].length > 200) {
                output[payload.R].shift();
            }

            if (typeof addCardConsole !== "undefined") { 
                addCardConsole(payload.R, payload.M);
            }            
            if (typeof addDetailedConsole !== "undefined") {
                if (payload.R == _active_repo) {
                    addDetailedConsole(payload.M);
                }
            }            
            if (typeof addEditorConsole !== "undefined") {
                if (payload.R == _active_repo) {
                    addEditorConsole(payload.M);
                }
            }            
        }
    };    
    wss.onopen = (event) => {
        wss_send("AUTH", sid);
    };    

    wss.onclose = (event) => {
        //window.location.href = '/'
        alert("Connection lost, reconnect!")
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
                js = JSON.parse(data)
                if (!js.AUTHED) {
                    setCookie('LK',false,365);
                    window.location.href = '/'
                    return;
                }
                callback(js);
            } else {
                alert(data)
            }
        }
    );    
}

function ajax_load(id, file, donehandler=false) {
    $('#' + id).html('<div style="text-align:center"><div class="spinner-border" style="width: 3rem; height: 3rem;" role="status"><span class="visually-hidden">Loading...</span></div></div>');
    $.get(file, function( data ) {
        $('#' + id).html(data);
        if (donehandler) donehandler();
    });
    return false;
}

function setTitle(text) {
    if ($( document ).width() < 1000)
        text = truncateString(text,15);
    $('#brand').html('<img src="img/pytainer.png" width="30" height="30" class="d-inline-block align-top" alt="" style="margin-right:10px">' + text)
}

function truncateString(str, num) {
    // If the length of str is less than or equal to num
    // just return str--don't truncate it.
    if (str.length <= num) {
      return str
    }
    // Return str truncated with '...' concatenated to the end of str.
    return str.slice(0, num) + '...'
}

function performanceRequestData() {
    api_request('performance',false, function(response) {
        _performance = response.DATA;
        displayPerformance();
    });

    setTimeout(() => {
        performanceRequestData();
    }, 5000);
}

function displayPerformance() {
    if ($('#perf_cpupercent').length) $('#perf_cpupercent').html(_performance.cpupercent.toFixed(2))
    if ($('#perf_cpuusage').length) $('#perf_cpuusage').html(_performance.cpuusage)
    if ($('#perf_ramusedpercent').length) $('#perf_ramusedpercent').html(_performance.ramusedpercent.toFixed(2))
    if ($('#perf_ramusedgb').length) $('#perf_ramusedgb').html(_performance.ramusedgb.toFixed(2))

    for (i in _performance.repos) {
        if ($('#cardperf_cpu_' + i).length) $('#cardperf_cpu_' + i).html(' ' + _performance.repos[i].cpu_time.toFixed(2))
        if ($('#cardperf_cpup_' + i).length) $('#cardperf_cpup_' + i).html(' ' + _performance.repos[i].cpu_percent.toFixed(2) + '%')
        if ($('#cardperf_status_' + i).length) $('#cardperf_status_' + i).html(' ' + _performance.repos[i].status)
    }
}

function scrollToAnchor(aid){
    var aTag = $("a[name='"+ aid +"']");
    $('html,body').animate({scrollTop: aTag.offset().top-70},'fast');
}

/**
 * Convert a string to HTML entities
 */
String.prototype.toHtmlEntities = function() {
    return this.replace(/./gm, function(s) {
        // return "&#" + s.charCodeAt(0) + ";";
        return (s.match(/[a-z0-9\s]+/i)) ? s : "&#" + s.charCodeAt(0) + ";";
    });
};

/**
 * Create string from HTML entities
 */
String.fromHtmlEntities = function(string) {
    return (string+"").replace(/&#\d+;/gm,function(s) {
        return String.fromCharCode(s.match(/\d+/gm)[0]);
    })
};


function showModalInput(title, message, callback) {
    $('#modalinputlabel').html(title)
    $('#modalinputmessage').html(message)
    _modalinputcallback = callback;
    $('#modalinputtext').val('');
    $('#exampleModal').modal('show');
}

function modalInputResponse() {
    if (_modalinputcallback) {
        _modalinputcallback($('#modalinputtext').val())
    }
    $('#exampleModal').modal('hide');
}


function auth(loginkey = false) {
    if (!loginkey) {
      api_request('auth', {'username': $('#username').val(), 'password': $('#password').val()}, function(response) {
          if (response['OK']) {
              if($("#permanentlogin").is(':checked')) {
                  setCookie('LK', response['LK'], 365);
              } else {
                setCookie('LK', false, 365);
              }
              ajax_load('body', 'tpl/framework.html')
          } else {
            setCookie('LK', false, 365);
          }
      }) 
    } else {
      api_request('authlk', {'loginkey': loginkey}, function(response) {
          if (response['OK']) {
              ajax_load('body', 'tpl/framework.html')
          } else {
            setCookie('LK', false, 365);
          }
      }) 
    }
}

function logout() {
    setCookie('LK', false, 365);
    window.location.href = '/';   
    return false; 
}

function setCookie(name,value,days) {
    var expires = "";
    if (days) {
        var date = new Date();
        date.setTime(date.getTime() + (days*24*60*60*1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "")  + expires + "; path=/";
}
function getCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}

function pyTainerCtrl(method, payload = false) {
    if (method == 'restart') {
        api_request('pytainerrestart', false, function(response) {}) 
    }
}