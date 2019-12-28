// NOTE: username is embedded in chat.html under script tag
document.addEventListener("DOMContentLoaded", () => {
    // connect to websocket
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
    let channel = "Lounge";

    console.log("current user is " + username); //debug
    console.log("current channel is " + channel); //debug

    // when connected, configure client side
    socket.on('connect', function(){
            joinChannel();
    });

    socket.on('message', data => {
        console.log("we are now back on message event in client");

        const p = document.createElement('p');
        const span_username = document.createElement('span');
        const br = document.createElement('br');
        const span_timestamp = document.createElement('span');

        if (data.username) {
            span_username.innerHTML = data.username;
            span_timestamp.innerHTML = data.timestamp;
            p.innerHTML = span_username.innerHTML + br.outerHTML + data.msg + br.outerHTML + span_timestamp.innerHTML; // br is an object, br.outerHTML is str

            console.log("p is" + p); //debug

            document.querySelector("#display-message-section").append(p);
        } else {
            printSysMsg(data.msg);
        }
    });

    // Send message
    document.querySelector("#send-message").onclick = () => {
        console.log(document.querySelector("#user-message").value); //debug
        socket.send({"msg": document.querySelector("#user-message").value, "username": username, "channel": channel});

        // clear the input area
        document.querySelector("#user-message").value = "";
    }

    // Channel selection
    document.querySelectorAll(".select-channel").forEach(p => {
        var msg;
        
        p.onclick = () => {
            let newChannel = p.innerHTML;
            console.log("You are clicking a new channel -> " + newChannel); //debug
            
            if (newChannel === channel) {
                msg = `You are already in the channel ${newChannel}`;
                printSysMsg(msg);
            } else {
                console.log("you were in a different channel -> " + channel); //debug
                leaveChannel(channel); // leave current channel
                channel = newChannel; // update current channel to new channel
                joinChannel(channel);  // join new channel
            }
        };
    });

    // print system message when user joins or leaves a channel
    var printSysMsg = function(msg) {
        const p = document.createElement('p');
        p.innerHTML = msg;
        document.querySelector("#display-message-section").append(p);
    };

    // leave a channel
    var leaveChannel = function() {
        // emits a message containing at least 'username' and 'channel' to server event 'leave'
        // use emit since it's a custom event because send will lead to 'message' bucket
        var data = {'username': username, 'channel': channel}; //debug
        console.log("leaving " + data.channel); //debug
        socket.emit('leave', {'username': username, 'channel': channel});

    };

    // join a channel
    var joinChannel = function() {
        // emits a message containing at least 'username' and 'channel' to server event 'join'
        // use emit since it's a custom event because send will lead to 'message' bucket
        var data = {'username': username, 'channel': channel}; //debug
        console.log("joining " + data.channel); //debug
        socket.emit('join', {'username': username, 'channel': channel});

        // clear message in display-message-section to start a new chat
        document.querySelector("#display-message-section").innerHTML = '';
    };
});