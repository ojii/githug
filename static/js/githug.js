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

GitHug.realtime = function(target, app_id, channel, event){
    var pusher = new Pusher(app_id);
    var channel = pusher.subscribe(channel);
    var loop = new GitHug.Loop();
    loop.start(5000);
    loop.addEvent('next', function(hug){
        new Fx.Tween(target, {
            'property': 'opacity'
        }).start(1, 0).addEvent('complete', function(){
            target.set('html', '<a href="' + hug.hugger.url + '">' + hug.hugger.name + '</a> hugged <a href="' + hug.hugged.url + '">' + hug.hugged.name + '</a>');
            new Fx.Tween(target, {
               'property': 'opacity'
            }).start(0, 1);
        });
    });
    channel.bind(event, function (data) {
        loop.append(data);
    });
    return loop;
};
