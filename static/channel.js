document.addEventListener("DOMContentLoaded", function() {
    // connect to websocket
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    // when connected, configure client side
    socket.on('connect', function(){
        // joined
        // joined via creating new channel by clicking/submitting form

        // joined via creating new channel by pressing enter key
        document.querySelector("#create-form").addEventListener("keypress", function(event) {
            if (event.keyCode == 13 || event.which == 33) {
                //socket.emit("joined");
                console.log("created channel")
            }
        });

    });
});