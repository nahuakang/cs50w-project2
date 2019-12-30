# Run "flask run --no-reload"
import os

from time import localtime, strftime
from functools import wraps
from collections import deque

from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
from flask_socketio import SocketIO, send, emit, join_room, leave_room

app = Flask(__name__)
app.config["SECRET_KEY"] = "something-unique" #os.getenv("SECRET_KEY")
app.config["SESSION_PERMANENT"] = True # or session.permanent=True
app.config['SESSION_TYPE'] = 'filesystem'
Session(app) # use Flask server-side session instead of default client-side session
socketio = SocketIO(app, manage_session=False) # give flask-socketio access to Session instead of forking

"""
    =====NOTE: Example of default Flask session behavior=====
    Before closing window: {'currentChannel': 'Games', 'username': 'nahua'}
    Closing window: "GET /socket.io/?EIO=3&transport=websocket&sid=12cdda1286724c849d3c9a4267f24422 HTTP/1.1" 200 0 236.749883
    After reopening window: <SecureCookieSession {'currentChannel': 'Lounge', 'username': 'nahua'}>

    =====REASON: FLASK-SOCKETIO ACCESS TO FLASK'S CONTEXT GLOBALS=====
    "A copy of the user session at the time the SocketIO connection is established is
    made available to handlers invoked in the context of that connection. If a SocketIO
    handler modifies the session, the modified session will be preserved for future
    SocketIO handlers, but regular HTTP route handlers will not see these changes.
    Effectively, when a SocketIO handler modifies the session, a “fork” of the session
    is created exclusively for these handlers."

    "When using server-side sessions such as those provided by the Flask-Session or
    Flask-KVSession extensions, changes made to the session in HTTP route handlers can
    be seen by SocketIO handlers, as long as the session is not modified in the SocketIO handlers."

    =====SOLUTION=====
    https://blog.miguelgrinberg.com/post/flask-socketio-and-the-user-session
    ```
    app.config['SESSION_TYPE'] = 'filesystem'
    Session(app)
    socketio = SocketIO(app, manage_session=False)
    ```
    With the above configuration, the server will create a subdirectory called flask_session in the
    current directory and write user sessions for all clients in it. These files will be written to
    by Flask or by Flask-SocketIO whenever changes to the session are made.

    If you set manage_session=True instead, the user sessions will continue to be forked as described
    above, regardless of what type of session you use.

    =====BUG=====
    There is still a bug:
    If after closing the window, the user directly accesses http://127.0.0.1:5000/create,
    the user will not be directed to the new channel but instead the one before closing window.
"""

"""GLOBAL VARIABLES"""
usernames = []
channels = ["Lounge", "News", "Games", "Coding"]

# Initialize history for  original channels
chatHistory = {n: deque(maxlen=100) for n in channels}


# Login Required: https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
def login_required(f):
    @wraps(f)

    def decorated_function(*args, **kwargs):

        if session.get("username") is None:
            return redirect(url_for("signin"))

        return f(*args, **kwargs)
    return decorated_function


def debug(fnName):
    print("\n")
    print(f"<--- SERVER ROUTER {fnName} --->")

    if session.get("username") is None:
        print("<--- username: NONE --->")
    else:
        print(f"<--- username: {session['username']} --->")
    
    if session.get("currentChannel") is None:
        print("<--- currentChannel: NONE --->")
    else:
        print(f"<--- currentChannel: {session['currentChannel']} --->")

    print(f"FINALLY, full session information: {session}")
    
    print("\n")


def socketDebug(fnName, data):
    print("\n")
    print(f"<--- SOCKET EVENT {fnName} --->")

    if fnName == "leave":
        print(f"<--- Leave channel: {data['channel']} --->")
    elif fnName == "join":
        print(f"<--- Join channel: {data['channel']} --->")
        print(f"<--- Current channel: {session['currentChannel']} --->")
    elif fnName == "message":
        print(f"<--- Message in channel: {data['channel']} --->")
        print(f"<--- Message from user: {data['username']} --->")
        print(f"<--- Message content: {data['msg']} --->")

    print(f"FINALLY, full session information: {session}")

    print("\n")


@app.route("/")
@login_required
def index():
    return redirect(url_for("chat"))


@app.route("/signin", methods=["GET", "POST"])
def signin():
    debug("signin")

    if request.method == "POST":
        # Get username from form submission
        username = request.form.get("username")

        # Check if username exists in usernames, which contains all logged-in users
        if username in usernames:
            return render_template("error.html", message="This username is taken.")

        # Update session['username'] and append username to logged-in users
        session["username"] = username
        usernames.append(username)

        # On signin, initialize channel to Lounge so chat.html always has a channel
        session['currentChannel'] = "Lounge"

        return redirect(url_for("chat"))

    elif request.method == "GET":
        return render_template("signin.html")


@app.route("/logout")
def logout(): 
    # remove username from usernames list, note potential erros include IndexError/ValueError
    try:
        usernames.remove(session['username'])
    except:
        print("\n Logout error. \n")

    # remove all Flask session cookies, i.e. username and currentChannel
    session.clear()

    return redirect(url_for("index"))


@app.route("/create", methods=["GET", "POST"])
def create():
    debug("create")

    if request.method == "POST":
        # Get newChannel from form submission
        newChannel = request.form.get("channel-name")

        # Update session currentChannel
        session['currentChannel'] = newChannel

        # if newChannel is new
        if newChannel not in channels:
            # add channel to created channels
            channels.append(newChannel)
            # create chatHistory for channel that holds the most recent 100 messages: https://stackoverflow.com/a/19723509/6297414
            chatHistory[newChannel] = deque(maxlen=100)

        return redirect(url_for("chat"))

    elif request.method == "GET":
        return render_template("create.html")


@app.route("/chat")
@login_required
def chat():
    debug("chat")
    return render_template("chat.html", channels=channels)


@socketio.on("join")
def join(data):
    join_room(data['channel'])

    # update socketio session currentChannel; has effect on flask session currentChannel with manage_session=False
    session['currentChannel'] = data['channel']

    socketDebug("join", data)

    # convert chatHistory from deque to list for JSON serialization: https://stackoverflow.com/a/5773404/6297414
    channelHistory = list(chatHistory[data["channel"]])

    send({"msg": data["username"] + " has joined the channel " + data["channel"],
        "chatHistory": channelHistory}, room=data["channel"]) #only sends to data["room"]


@socketio.on("leave")
def leave(data):
    socketDebug("leave", data)

    leave_room(data['channel'])

    send({"msg": data["username"] + " has left the channel " + data["channel"]}, room=data["channel"])


@socketio.on("message")
def message(data):
    socketDebug("message", data)

    # automatically send to event "message" to clients: https://stackoverflow.com/a/13767655
    timestampedData = {"msg": data["msg"], "username": data["username"], "timestamp": strftime("%b-%d %I: %M%p", localtime())}
    
    send(timestampedData, room=data["channel"])

    chatHistory[data['channel']].append(timestampedData)


@socketio.on('connect')
def connect():
    print("\n")
    print(f"<--- SOCKET EVENT Connect --->")
    print(f"Full session information: {session}")
    print("\n")


@socketio.on('disconnect')
def disconnect():
    print("\n")
    print(f"<--- SOCKET EVENT Disconnect --->")
    print(f"Full session information: {session}")
    print("\n")


if __name__ == "__main__":
    socketio.run(app, debug=True)