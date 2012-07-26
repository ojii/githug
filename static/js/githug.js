var GitHug = GitHug || {};

GitHug.Loop = new Class({
    Implements: Events,
    initialize: function(){
        this.queue = [];
        this.timer = null;
    },
    start: function(interval){
        this.interval = interval;
        this.timer = setInterval(this.mainloop.bind(this), this.interval);
    },
    mainloop: function(){
        if (this.queue.length){
            this.next(this.queue.shift());
        }
    },
    append: function(item){
        this.queue.push(item);
    },
    next: function(item){
        this.fireEvent('next', item);
    }
});

GitHug.realtime = function(target, ws_url){
    if (!window.WebSocket){
        return;
    }
    var loop = new GitHug.Loop();
    loop.start(5000);
    loop.addEvent('next', function(hug){
        new Fx.Tween(target, {
            'property': 'opacity'
        }).start(1, 0).addEvent('complete', function(){
            target.set('text', hug.hugger.name + " hugged " + hug.hugged.name);
            new Fx.Tween(target, {
               'property': 'opacity'
            }).start(0, 1);
        });
    });
    var ws = new WebSocket(ws_url);
    ws.onmessage = function (msg) {
        var hug = JSON.parse(msg.data);
        loop.append(hug);
    };
};
