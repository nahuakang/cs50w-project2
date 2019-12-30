// NOTE: username and channel are embedded in chat.html under script tag
document.addEventListener("DOMContentLoaded", () => {

    var myStorage = window.localStorage;

    var debug = function() {
        console.log("\n");
        console.log("-var username- is " + username);
        console.log("-var channel- is " + channel);
        console.log("-myStorage.currentChannel- is " + myStorage.currentChannel);
        console.log("\n");
    };

    debug();

    // Connect to websocket
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    socket.on('connect', ()=> {

        console.log("client CONNECTED"); //debug

        // myStorage.currentChannel === null on first sign-in
        // if myStorage.currentChannel is not null, load that channel instead of lounge
        // NOTE BUG: closing window -> direct access http://127.0.0.1:5000/create will not lead to new channel; need to join manually
        if (myStorage.currentChannel) {
            joinChannel(myStorage.currentChannel);
            channel = myStorage.currentChannel; 
        } else {
            // default to the channel provided by chat.html, which always has a channel available
            joinChannel(channel);
        }

        debug();
    });

    // For messages from server that is delivered via send()
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

    // Select a Channel on Sidebar to Join a Channel
    document.querySelectorAll(".select-channel").forEach(p => {
        p.onclick = () => {

            debug();

            let newChannel = p.innerHTML;
            console.log("\nYou are clicking a new channel -> " + newChannel); //debug
            
            if (newChannel === channel) {
                let msg = `You are already in the channel ${newChannel}`;
                printSystemMessage(msg);
            } else {
                // Inform server to leave current channel
                leaveChannel(channel);

                // update current channel to new channel
                channel = newChannel;

                // Inform server to join new channel
                joinChannel(channel);
            }
        };
    });

    // Print system message when user joins or leaves a channel
    var printSystemMessage = function(msg) {
        const p = document.createElement('p');
        p.innerHTML = msg;
        document.querySelector("#display-message-section").append(p);
    };

    // Leave a channel
    var leaveChannel = function(channelName) {
        // emits a message containing at least 'username' and 'channel' to server event 'leave'
        // use emit since it's a custom event because send will lead to 'message' bucket
        console.log("Client leaves " + channelName); //debug
        
        socket.emit('leave', {'username': username, 'channel': channelName});
    };

    // Join a channel
    var joinChannel = function(channelName) {
        // emits a message containing at least 'username' and 'channel' to server event 'join'
        // use emit since it's a custom event because send will lead to 'message' bucket
        console.log("Client joins " + channelName); //debug

        myStorage.setItem("currentChannel", channelName);
        
        socket.emit('join', {'username': username, 'channel': channelName});

        // change heading to proper channel name
        var channelHeading = document.querySelector("#channel-name-content");
        channelHeading.innerText = channelName;

        // clear message in display-message-section to start a new chat
        document.querySelector("#display-message-section").innerHTML = '';

        // put autofocus on text box
        document.querySelector("#user-message").focus();
    };

    // Message wrapper
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

    // When log out, forget about myStorage's currentChannel
    document.querySelector('#logout').addEventListener('click', () => {
        myStorage.clear();
    });

    // Forget myStorage's currentChannel when clicked on '+ Channel'
    document.querySelector('#create-channel').addEventListener('click', () => {
        myStorage.removeItem('currentChannel');
    });
});