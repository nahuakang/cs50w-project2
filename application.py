# Run "flask run --no-reload"
import os

from functools import wraps

from flask import Flask, redirect, render_template, request, session, url_for
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

#app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False


"""GLOBAL VARIABLES"""
usernames = []
channels = []


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

        return redirect(url_for("index"))

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
            return render_template("error.html", message="This channel is already created.")

        channels.append(newChannel)

        return redirect("/channels/" + newChannel)

    elif request.method == "GET":
        return redirect(url_for("index"))


@app.route("/channels/<channel>", methods=["GET", "POST"])
@login_required
def enter(channel):
    if request.method == "GET":
        session["current_channel"] = channel
        return render_template("channel.html", channels=channels)

    elif request.method == "POST":
        return redirect(url_for("index"))
