import flask
import functools
import os
import sqlite3
import sys
import werkzeug.security
import werkzeug.utils

import nyaruhodo

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
DATABASE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db.sqlite3")
server = flask.Flask(__name__)
server.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
server.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024
server.secret_key = os.urandom(24)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_database():

    database = getattr(flask.g, "_database", None)

    if database is None:

        database = flask.g._database = sqlite3.connect(DATABASE_FILE)
        database.row_factory = sqlite3.Row

    return database

@server.route("/favicon.ico")

def favicon():

    return flask.send_from_directory(os.path.join(server.root_path, "static"), "favicon.png", mimetype="image/png")

@server.teardown_appcontext

def close_connection(exception):

    database = getattr(flask.g, "_database", None)

    if database is not None:

        database.close()

def initialise_database():

    with server.app_context():

        database = get_database()
        database.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL)")
        database.execute("CREATE TABLE IF NOT EXISTS logs (log_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, filename TEXT NOT NULL, filetype TEXT, status TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users (user_id))")
        database.commit()

def requirelogin(f):

    @functools.wraps(f)

    def decorated_function(*args, **kwargs):

        if "user_id" not in flask.session:

            return flask.redirect(flask.url_for("login"))

        return f(*args, **kwargs)

    return decorated_function

@server.route("/")

def index():

    return flask.render_template("index.html", user=flask.session.get("user_id"))

@server.route("/dashboard/register", methods=["GET", "POST"])

def register():

    if flask.request.method == "POST":

        username = flask.request.form["username"]
        password = flask.request.form["password"]
        database = get_database()

        try:

            hashed_password = werkzeug.security.generate_password_hash(password)
            database.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            database.commit()

            return flask.redirect(flask.url_for("login"))

        except sqlite3.IntegrityError:

            return flask.render_template("register.html", error="Sorry! Username is already taken.")

    return flask.render_template("register.html")

@server.route("/dashboard/login", methods=["GET", "POST"])

def login():

    if flask.request.method == "POST":

        username = flask.request.form["username"]
        password = flask.request.form["password"]
        database = get_database()
        user = database.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user and werkzeug.security.check_password_hash(user["password"], password):

            flask.session["user_id"]  = user["user_id"]
            flask.session["username"] = user["username"]
            return flask.redirect(flask.url_for("dashboard"))

        return flask.render_template("login.html", error="Sorry! Username or password is incorrect.")

    return flask.render_template("login.html")

@server.route("/dashboard/logout")

def logout():

    flask.session.clear()

    return flask.redirect(flask.url_for("index"))

@server.route("/dashboard")

@requirelogin

def dashboard():

    database = get_database()
    logs = database.execute("SELECT * FROM logs WHERE user_id = ? ORDER BY timestamp DESC", (flask.session["user_id"],)).fetchall()
    return flask.render_template("dashboard.html", username=flask.session["username"], logs=logs)

@server.route("/dashboard/scan", methods=["POST"])

def scan():

    if "file" not in flask.request.files:

        return flask.jsonify({"error": "Sorry! No file was uploaded."}), 400

    file = flask.request.files["file"]

    if file.filename == "":

        return flask.jsonify({"error": "Sorry! No file was selected."}), 400

    if file:

        filename  = werkzeug.utils.secure_filename(file.filename)
        filepath  = os.path.join(server.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        result       = nyaruhodo.core.scan(filepath, filename)
        detected_type = result.get("filetype")
        metadata     = nyaruhodo.properties.read(filepath, detected_type)

        if metadata:

            result["metadata"] = metadata

        if result["mismatch"] and flask.request.form.get("virustotal") == "true":

            virustotal = nyaruhodo.services.virus_total(filepath)
            result["virustotal"] = virustotal

        if "user_id" in flask.session:

            database = get_database()

            if result["filetype"] == "UNKNOWN":

                summary = "Unknown"

            elif result["mismatch"]:

                summary = "Mismatch"

            else:

                summary = "Match"

            database.execute("INSERT INTO logs (user_id, filename, filetype, status) VALUES (?, ?, ?, ?)", (flask.session["user_id"], filename, result["filetype"], summary))
            database.commit()

        return flask.jsonify(result)

    return flask.jsonify({"error": "Sorry! Processing failed."}), 500

if __name__ == "__main__":

    nyaruhodo.init.paint_screen()
    initialise_database()
    server.run(debug=True, host="0.0.0.0", port=5000)