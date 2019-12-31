# Project 2

Web Programming with Python and JavaScript

## NOTE: Example of default Flask session behavior
Before closing window: `{'currentChannel': 'Games', 'username': 'nahua'}`
Closing window: `"GET /socket.io/?EIO=3&transport=websocket&sid=12cdda1286724c849d3c9a4267f24422 HTTP/1.1" 200 0 236.749883`
After reopening window: `<SecureCookieSession {'currentChannel': 'Lounge', 'username': 'nahua'}>`

### REASON: FLASK-SOCKETIO ACCESS TO FLASK'S CONTEXT GLOBALS
"A copy of the user session at the time the SocketIO connection is established is
made available to handlers invoked in the context of that connection. If a SocketIO
handler modifies the session, the modified session will be preserved for future
SocketIO handlers, but regular HTTP route handlers will not see these changes.
Effectively, when a SocketIO handler modifies the session, a “fork” of the session
is created exclusively for these handlers."

"When using server-side sessions such as those provided by the Flask-Session or
Flask-KVSession extensions, changes made to the session in HTTP route handlers can
be seen by SocketIO handlers, as long as the session is not modified in the SocketIO handlers."

### SOLUTION
Referencing this link: https://blog.miguelgrinberg.com/post/flask-socketio-and-the-user-session
```
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
socketio = SocketIO(app, manage_session=False)
```
"With the above configuration, the server will create a subdirectory called flask_session in the
current directory and write user sessions for all clients in it. These files will be written to
by Flask or by Flask-SocketIO whenever changes to the session are made.

If you set manage_session=True instead, the user sessions will continue to be forked as described
above, regardless of what type of session you use."

### BUG
There is still a bug:
If after closing the window, the user directly accesses http://127.0.0.1:5000/create,
the user will not be directed to the new channel but instead the one before closing window.