# CS50W Project 2: Flack Chat App

[Project 2 Instructions](https://docs.cs50.net/ocw/web/projects/2/project2.html)

This Flack chat app is implemented using Python, [Flask](https://www.palletsprojects.com/p/flask/) framework, and Miguel Grinberg's [Flask-SocketIO](https://flask-socketio.readthedocs.io/en/latest/) on the server side, and vanilla Javascript as well as [SocketIO](https://socket.io/) on the client side.

## My Flack App Screenshot
<img src="https://github.com/nahuakang/cs50w-project2/blob/master/static/screenshot.png" width="500">

## Usage
1. Sign in with a username (no registration required)
2. You are automatically in the Lounge channel
3. Switch channel by clicking on a channel on the sidebar to the left
4. Create a new channel by clicking the *+Channel* button on the sidebar to the left
5. Send private message to another user by clicking the user on the sidebar to the left (buggy)
6. Logout

## Features
1. Any user can see four basic channels and can create any new channels.
2. Any user can see other online users (requires refreshing the page).
3. The most recent 100 chat messages in any public channels will be saved.
4. After closing the window and re-enter the chat url, the user is redirected back to their last seen channel.
5. Messages sent in the chat app have timestamp and the username attached (with color schemes).
6. Users can send private, 1-on-1 messages to other users (buggy since the private message will display on any channel that is on the the recipient's screen).

## Setup
```
# Clone repo
$ git clone https://github.com/nahuakang/cs50w-project2.git

$ cd cs50-project2

# Create a conda env (Preferred). Alternatively use venv and pip install
$ conda create --name cs50-project2 python=3

# Activate the Conda env
$ conda activate cs50-project2

# Install all dependencies
$ conda install --file requirements.txt

# ENV Variables
$ export FLASK_APP = application.py

# Run the application
$ python application.py
```

## Features Not Implemented (Nice-to-Have's)
1. The chat app is not responsive.
2. The channel and user updates on the sidebar requires reloading the page.

## BUGS
There is still a bug:
If after closing the window, the user directly accesses http://127.0.0.1:5000/create,
the user will not be directed to the new channel but instead the one before closing window.

## Additional Notes: On Flask's default session behavior with Flask-SocketIO
I encountered a problem with Flask's default session when using Flask-SocketIO. Basically, changing the key-values in session does not seem to work when the call is made under a socketio handler:
```
Before closing window: `{'currentChannel': 'Games', 'username': 'nahua'}`
Closing window: `"GET /socket.io/?EIO=3&transport=websocket&sid=12cdda1286724c849d3c9a4267f24422 HTTP/1.1" 200 0 236.749883`
After reopening window: `<SecureCookieSession {'currentChannel': 'Lounge', 'username': 'nahua'}>`
```

Solution and reasons see below.

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

## REFERENCES
This project benefits greatly from the following resources:
1. [Official Flask-SocketIO documentation](https://flask-socketio.readthedocs.io/en/stable/)
2. [Create Chat Applicaton Using Flask-SocketIO - Chat App Part12](https://www.youtube.com/watch?v=zQDzNNt6xd4)
3. [Flask-SocketIO Session IDs and Private Messages](https://www.youtube.com/watch?v=mX7hPZidPPY)
4. [Flask-SocketIO and the User Session](https://blog.miguelgrinberg.com/post/flask-socketio-and-the-user-session)
5. [Flask-SocketIO sessions](https://github.com/miguelgrinberg/Flask-SocketIO/blob/master/example/sessions.py)

Other resources, such as tips from StackOverflow, are mostly included in the individual files as comments.