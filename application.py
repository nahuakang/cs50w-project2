# Run "flask run --no-reload"
import os

from time import localtime, strftime
from functools import wraps

from flask import Flask, redirect, render_template, request, session, url_for
from flask_socketio import SocketIO, send, emit, join_room, leave_room

app = Flask(__name__)
app.config["SECRET_KEY"] = "something-unique" #os.getenv("SECRET_KEY")
socketio = SocketIO(app)

#app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False


"""GLOBAL VARIABLES"""
usernames = []
channels = ["Lounge", "News", "Games", "Coding"]


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
    return render_template("index.html", channels=channels)


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        username = request.form.get("username")
        
        # Check if username exists in usernames
        if username in usernames:
            return render_template("error.html", message="This username is taken.")

        session["username"] = username
        usernames.append(username)
        # https://stackoverflow.com/a/55055558
        session.permanent = True

        return redirect(url_for("chat"))

    elif request.method == "GET":
        return render_template("signin.html")


@app.route("/logout")
def logout():
    # remove the username from the session if it's there
    try:
        usernames.remove(session['username'])
    except ValueError:
        pass
    
    # remove cookie
    session.clear()

    return redirect(url_for("index"))


@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        newChannel = request.form.get("channel-name")

        if newChannel in channels:
            return redirect(url_for("chat"))

        channels.append(newChannel)
        session["currentChannel"] = newChannel

        return redirect(url_for("chat"))

    elif request.method == "GET":
        return redirect(url_for("index"))


@app.route("/chat", methods=["GET", "POST"])
@login_required
def chat():
    return render_template("chat.html", channels=channels, username=session["username"])


@socketio.on("join")
def join(data):
    print(f"\n\n{data}\n\n") #debug
    # current channel has to be sent from the client
    join_room(data['channel'])
    send({"msg": data["username"] + " has joined the channel " + data["channel"]}, room=data["channel"]) #only sends to data["room"]


@socketio.on("leave")
def leave(data):
    print(f"\n\n trying to leave the room with data: {data}\n\n") #debug
    leave_room(data['channel'])
    send({"msg": data["username"] + " has left the channel " + data["channel"]}, room=data["channel"])


@socketio.on("message")
def message(data):
    print(f"\n\n msg is {data['msg']} \n username is {data['username']} \n channel is {data['channel']}\n\n") #debug
    # automatically send to event "message" to clients: https://stackoverflow.com/a/13767655
    send({"msg": data["msg"], "username": data["username"], "timestamp": strftime("%b-%d %I: %M%p", localtime())}, room=data["channel"])
    print("message sent via socketio back to client") #debug


if __name__ == "__main__":
    socketio.run(app, debug=True)