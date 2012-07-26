var GitHug = GitHug || {};

GitHug.realtime = function(target, ws_url){
    if (!window.WebSocket){
        return;
    }
    var ws = new WebSocket(ws_url);
    ws.onmessage = function (msg) {
        var hug = JSON.parse(msg.data);
        console.log(hug.hugger.name + " hugged " + hug.hugged.name);
    };
};
