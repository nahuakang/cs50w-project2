# Run "flask run --no-reload"
import os

from time import localtime, strftime
from functools import wraps
from collections import deque

from flask import Flask, redirect, render_template, request, session, url_for
from flask_socketio import SocketIO, send, emit, join_room, leave_room

app = Flask(__name__)
app.config["SECRET_KEY"] = "something-unique" #os.getenv("SECRET_KEY")
socketio = SocketIO(app)

#app.config["SESSION_TYPE"] = "filesystem"
#app.config["SESSION_PERMANENT"] = False


"""GLOBAL VARIABLES"""
usernames = []
channels = ["Lounge", "News", "Games", "Coding"]

# Initialize history for  original channels
chatHistory = {n: deque(maxlen=100) for n in channels}


# Login Required Decorator
# See https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
def login_required(f):
    @wraps(f)

    def decorated_function(*args, **kwargs):

        if session.get("username") is None:
            return redirect(url_for("signin"))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
@login_required
def index():
    # NOTE: session drops 'currentChannel' after window closes: 
    # Before window close: {'username': 'nahua', 'currentChannel': 'News'} 
    # After window close and reload: <SecureCookieSession {'username': 'nahua'}>
    # Use client side localStorage to redirect chat.html to the channel previously on
    return redirect(url_for("chat"))


@app.route("/signin", methods=["GET", "POST"])
def signin():
    print("\ngoing through /signin to redirect to chat\n") #debug
    print(f"\n Before signin, these users are logged in: {usernames} \n") #debug

    if request.method == "POST":
        username = request.form.get("username")
        
        # Check if username exists in usernames
        if username in usernames:
            return render_template("error.html", message="This username is taken.")

        session["username"] = username
        usernames.append(username)

        # https://stackoverflow.com/a/55055558
        #session.permanent = True

        return redirect(url_for("chat"))

    elif request.method == "GET":
        return render_template("signin.html")


@app.route("/logout")
def logout(): 
    # remove username from usernames list, note potential IndexError/ValueError
    try:
        usernames.remove(session['username'])
    except:
        print("\n Logout error. \n")

    # remove cookie
    session.clear()

    return redirect(url_for("index"))


@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        newChannel = request.form.get("channel-name")

        if newChannel in channels:
            session['currentChannel'] = newChannel
            
            return redirect(url_for("chat"))

        channels.append(newChannel)

        # Set currentChannel to new channel for chat.html
        session["currentChannel"] = newChannel

        # collections.deque with maxlen: https://stackoverflow.com/a/19723509/6297414 
        chatHistory[newChannel] = deque(maxlen=100)

        return redirect(url_for("chat"))

    elif request.method == "GET":
        return render_template("create.html")


@app.route("/chat", methods=["GET", "POST"])
@login_required
def chat():
    return render_template("chat.html", channels=channels, username=session["username"])


@socketio.on("join")
def join(data):
    # current channel has to be sent from the client
    join_room(data['channel'])

    # update session currentChannel
    session["currentChannel"] = data['channel']

    print(f"\n server join event current channel changed to: {session['currentChannel']} \n") #debug
    print(f"\n AFTER JOIN, session info: {session} \n")
    print(f"\n Right now, these users are logged in: {usernames} \n") #debug

    # convert chatHistory from deque to list for JSON serialization: https://stackoverflow.com/a/5773404/6297414
    channelHistory = list(chatHistory[data["channel"]])

    send({"msg": data["username"] + " has joined the channel " + data["channel"],
        "chatHistory": channelHistory}, room=data["channel"]) #only sends to data["room"]


@socketio.on("leave")
def leave(data):
    print(f"\n leaving the channel: {data['channel']} \n") #debug
    
    leave_room(data['channel'])

    send({"msg": data["username"] + " has left the channel " + data["channel"]}, room=data["channel"])


@socketio.on("message")
def message(data):
    # automatically send to event "message" to clients: https://stackoverflow.com/a/13767655
    timestampedData = {"msg": data["msg"], "username": data["username"], "timestamp": strftime("%b-%d %I: %M%p", localtime())}
    
    send(timestampedData, room=data["channel"])

    chatHistory[data['channel']].append(timestampedData)


if __name__ == "__main__":
    socketio.run(app, debug=True)