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

# GLOBAL VARIABLES
usernames = dict()
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
    print(f"<--- SESSION: {session} --->")
    print("\n")


def socketDebug(fnName, *args):
    print("\n")
    print(f"<--- SOCKET EVENT {fnName} --->")
    if args:
        print(f"<--- SOCKET DATA {args[0]} --->")
    print(f"<--- SESSION: {session} --->")
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
        session['username'] = username
        usernames[username] = None # add username with value None to logged-in user list

        # On signin, initialize channel to Lounge so chat.html always has a channel
        session['currentChannel'] = "Lounge"

        return redirect(url_for("chat"))

    elif request.method == "GET":
        return render_template("signin.html")


@app.route("/logout")
def logout(): 
    # First remove username from usernames dict
    usernames.pop(session['username'], None)

    # Second, remove Flask session cookies, i.e. username and currentChannel
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

        # If newChannel is new
        if newChannel not in channels:
            # Add channel to created channels
            channels.append(newChannel)
            # Create chatHistory for channel that holds the most recent 100 messages: https://stackoverflow.com/a/19723509/6297414
            chatHistory[newChannel] = deque(maxlen=100)

        return redirect(url_for("chat"))

    elif request.method == "GET":
        return render_template("create.html")


@app.route("/chat")
@login_required
def chat():
    debug("chat")

    # Pass the lists of channels as well as usernames to chat.html for rendering sidebar
    return render_template("chat.html", channels=channels, usernames=usernames)


@socketio.on("join")
def join(data):
    join_room(data['channel'])

    # Update socketio session currentChannel; has effect on flask session currentChannel with manage_session=False
    session['currentChannel'] = data['channel']

    socketDebug("join", data)

    # Convert chatHistory from deque to list for JSON serialization: https://stackoverflow.com/a/5773404/6297414
    channelHistory = list(chatHistory[data["channel"]])

    send({"username": data['username'], "msg": " has joined the channel " + data['channel'],
        "chatHistory": channelHistory}, room=data["channel"]) #only sends to data["room"]


@socketio.on("leave")
def leave(data):
    socketDebug("leave", data)

    leave_room(data['channel'])

    send({"username": data['username'], "msg": " has left the channel " + data['channel']}, room=data['channel'])


@socketio.on("message")
def message(data):
    socketDebug("message", data)

    # If message is public, send to the correct channel
    if data['privateMode'] == 'false':
        # automatically send to event "message" to clients: https://stackoverflow.com/a/13767655
        # # Note: format time to "Dec 31, 2019, 04:11 PM"
        timestampedData = {"msg": data["msg"], "username": data["username"], "timestamp": strftime("%b %d, %Y %I:%M %p", localtime())}
        send(timestampedData, room=data["channel"])
        chatHistory[data['channel']].append(timestampedData)

    # If message is private, send to the correct user session id
    elif data['privateMode'] == 'true':
        timestampedData = {"msg": data["msg"], "username": data["fromUser"], "timestamp": strftime("%b %d, %Y %I:%M %p", localtime()), "private": True}
        send(timestampedData, room=usernames[data["toUser"]])


@socketio.on('connect')
def connect():
    # Set or update userID for the logged-in user list
    # Note request.sid changes every time the user disconnects and connects to the socket
    usernames[session['username']] = request.sid #debug

    socketDebug('connect')


@socketio.on('disconnect')
def disconnect():
    socketDebug('disconnect')


if __name__ == "__main__":
    socketio.run(app, debug=True)