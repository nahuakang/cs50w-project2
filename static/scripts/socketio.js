// NOTE: username and channel are embedded in chat.html under script tag
document.addEventListener("DOMContentLoaded", () => {

    var myStorage = window.localStorage;

    var debugChannel = function() {
        console.log("\n");
        console.log("-var username- is " + username);
        console.log("-var channel- is " + channel);
        console.log("-myStorage.currentChannel- is " + myStorage.currentChannel);
        console.log("-myStorage.privateMode- is " + myStorage.privateMode);
        console.log("\n");
    };

    debugChannel();

    // Connect to websocket
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    socket.on('connect', ()=> {
        console.log("client CONNECTED"); //debug

        // myStorage.currentChannel === null on first sign-in; booleans are stored as strings in localStorage
        // if myStorage.currentChannel is not null, load that channel instead of lounge
        if (myStorage.currentChannel) {
            if (myStorage.privateMode === "false") {
                joinChannel(myStorage.currentChannel);
                channel = myStorage.currentChannel;
            } else if (myStorage.privateMode === "true") {
                joinPrivateChannel(myStorage.currentChannel);
                channel = myStorage.currentChannel;
            }
        } else {
            // default to the channel provided by chat.html, joinChannel()/joinPrivateChannel() will set myStorage values
            joinChannel(channel);
        }
    });

    // Default 'message' Controller: handles 3 types of messages from server that is delivered via send(): message, join, leave
    socket.on('message', data => {
        console.log("we are now back on message event in client"); //debug

        if (data.chatHistory) {
            // JOIN: if data.chatHistory exists, it is for server event 'join' via flask-socketio send
            // Load the maximum 100 messages to the channel
            for (let i = 0; i < data.chatHistory.length; i++) {
                formatMessage(data.chatHistory[i]);
            }

            // Load the announcement that the user has joined the channel
            printSystemMessage(data.msg);

        } else if (data.username) {
            // MESSAGE: filter as message if data.username existing
            formatMessage(data);
            console.log("Message is sent by " + data.username); //debug

        } else {
            // LEAVE: For server event 'leave' via flask-socketio send
            printSystemMessage(data.msg);
        }
    });

    // Select a Channel on Sidebar to Join a Channel
    document.querySelectorAll(".select-channel").forEach(p => {
        p.onclick = () => {
            let newChannel = p.innerHTML;
            
            if (newChannel === channel) {
                let msg = `You are already in the channel ${newChannel}`;
                printSystemMessage(msg);
            } else {
                leaveChannel(channel);
                channel = newChannel;
                joinChannel(channel);
            }
        };
    });

    // Select a user on Sidebar to start private message
    document.querySelectorAll(".select-private-channel").forEach(p => {
        p.onclick = () => {
            let toUser = p.innerHTML;

            if (toUser == channel) {
                let msg = `You are already in the private channel with ${toUser}`;
                printSystemMessage(msg);
            } else {
                leaveChannel(channel);
                channel = toUser;
                joinPrivateChannel(toUser);
            }
        };
    });

    // Send message button click
    document.querySelector("#send-message").onclick = () => {
        console.log(document.querySelector("#user-message").value); //debug

        // send to public channel
        if (myStorage.privateMode === "false") {
            const message = {"msg": document.querySelector("#user-message").value, "username": username, "channel": channel, "privateMode": "false"};
            console.log(message); //debug
            socket.send(messsage);

        } else if (myStorage.privateMode === "true") {
            const message = {"msg": document.querySelector("#user-message").value, "fromUser": username, "toUser": channel, "privateMode": "true"};
            console.log(message); //debug
            socket.send(message);

            // Display the message to the sender as well
            let data = {'msg': document.querySelector("#user-message").value,'username': username,'timestamp': formatTimeStamp()};
            formatMessage(data);
        }

        // clear the input area
        document.querySelector("#user-message").value = "";
    };

    // Print system message when user joins or leaves a channel
    var printSystemMessage = function(msg) {
        const p = document.createElement('p');
        p.innerHTML = msg;
        document.querySelector("#display-message-section").append(p);
    };

    // Leave a channel
    var leaveChannel = function(channelName) {
        // emits a message containing at least 'username' and 'channel' to server event 'leave'
        console.log("Client leaves " + channelName); //debug
        socket.emit('leave', {'username': username, 'channel': channelName});
    };

    // Join a public channel
    var joinChannel = function(channelName) {
        // Emits a message containing at least 'username' and 'channel' to server event 'join'
        console.log("Client joins " + channelName); //debug

        myStorage.setItem("currentChannel", channelName);
        myStorage.setItem("privateMode", false);

        socket.emit('join', {"username": username, "channel": channelName});

        // Change heading to proper channel name
        var channelHeading = document.querySelector("#channel-name-content");
        channelHeading.innerText = channelName;

        // Clear message in display-message-section to start a new chat
        document.querySelector("#display-message-section").innerHTML = '';

        // Put autofocus on text box
        document.querySelector("#user-message").focus();
    };

    // Join a private channel (message between two users)
    var joinPrivateChannel = function(toUser) {
        console.log("Client joins private channel with " + toUser); //debug

        myStorage.setItem("currentChannel", toUser);
        myStorage.setItem("privateMode", true);

        // Change heading in #display-message-section to the proper private channel name
        var channelHeading = document.querySelector("#channel-name-content");
        channelHeading.innerText = toUser;

        // Clear message in display-message-section to start a new chat
        document.querySelector("#display-message-section").innerHTML = '';
        printSystemMessage("You can now talk to " + toUser + " privately.");

        // Put autofocus on text box
        document.querySelector("#user-message").focus();
    };

    // Message wrapper
    var formatMessage = function(data) {
        const p = document.createElement('p');
        const span_username = document.createElement('span');
        const br = document.createElement('br');
        const span_timestamp = document.createElement('span');

        span_username.innerHTML = data.username;
        span_timestamp.innerHTML = data.timestamp;
        p.innerHTML = span_username.innerHTML + br.outerHTML + data.msg + br.outerHTML + span_timestamp.innerHTML; // br is an object, br.outerHTML is str

        document.querySelector("#display-message-section").append(p);
    }

    var formatTimeStamp = function() {
        // Reference: https://stackoverflow.com/a/46935603/6297414
        let options = {month: "short",  day: "numeric", hour: "2-digit", minute: "2-digit"};
        let date = new Date();
        return date.toLocaleDateString("en-us", options);
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