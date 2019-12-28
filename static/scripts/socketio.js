// NOTE: username and channel are embedded in chat.html under script tag
document.addEventListener("DOMContentLoaded", () => {

    console.log("current user is " + username); //debug

    // connect to websocket
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    socket.on('connect', ()=> {
        // Remember channel before closing window via localStorage as Flask session does not save custom 'currentChannel' key
        channel = window.localStorage.getItem("currentChannel");

        if (channel) {
            joinChannel(channel);
        } else {
            channel = "Lounge";
            window.localStorage.setItem("currentChannel", channel);
            joinChannel(channel);
        }
    });

    socket.on('message', data => {
        console.log("we are now back on message event in client"); //debug

        if (data.chatHistory) {
            // if data.chatHistory exists, it is for server event 'join' via flask-socketio send
            // first load the maximum 100 messages to the channel
            for (let i = 0; i < data.chatHistory.length; i++) {
                formatMessage(data.chatHistory[i]);
            }

            // then load the announcement that the user has joined the channel
            printSystemMessage(data.msg);

        } else if (data.username) {
            formatMessage(data);

        } else {
            // finally, it should be for server event 'leave' via flask-socketio send
            printSystemMessage(data.msg);
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
                printSystemMessage(msg);
            } else {
                leaveChannel(channel); // leave current channel
                channel = newChannel; // update current channel to new channel
                joinChannel(channel);  // join new channel
            }
        };
    });

    // print system message when user joins or leaves a channel
    var printSystemMessage = function(msg) {
        const p = document.createElement('p');
        p.innerHTML = msg;
        document.querySelector("#display-message-section").append(p);
    };

    // leave a channel
    var leaveChannel = function(channel) {
        // emits a message containing at least 'username' and 'channel' to server event 'leave'
        // use emit since it's a custom event because send will lead to 'message' bucket
        var data = {'username': username, 'channel': channel}; //debug
        console.log("leaving " + channel); //debug
        socket.emit('leave', {'username': username, 'channel': channel});

    };

    // join a channel
    var joinChannel = function(channel) {
        // emits a message containing at least 'username' and 'channel' to server event 'join'
        // use emit since it's a custom event because send will lead to 'message' bucket
        var data = {'username': username, 'channel': channel}; //debug
        console.log("joining " + channel); //debug

        window.localStorage.setItem("currentChannel", channel);
        
        socket.emit('join', {'username': username, 'channel': channel});

        // change heading to proper channel name
        var channelHeading = document.querySelector("#channel-name-content");
        channelHeading.innerText = channel;

        // clear message in display-message-section to start a new chat
        document.querySelector("#display-message-section").innerHTML = '';

        // put autofocus on text box
        document.querySelector("#user-message").focus();
    };

    var formatMessage = function(data) {
        // Create message skeleton
        const p = document.createElement('p');
        const span_username = document.createElement('span');
        const br = document.createElement('br');
        const span_timestamp = document.createElement('span');

        // populate and construct message
        span_username.innerHTML = data.username;
        span_timestamp.innerHTML = data.timestamp;
        p.innerHTML = span_username.innerHTML + br.outerHTML + data.msg + br.outerHTML + span_timestamp.innerHTML; // br is an object, br.outerHTML is str

        // display message to channel
        document.querySelector("#display-message-section").append(p);
    }
});