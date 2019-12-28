document.addEventListener("DOMContentLoaded", () => {
    // make 'enter' key equivalent to send message button
    let msg = document.querySelector("#user-message");
    msg.addEventListener("keyup", event => {
        if (event.keyCode === 13 || event.which === 13) {
            document.querySelector("#send-message").click();
        }
    });
});