import flask
import functools
import os
import sqlite3
import werkzeug.security
import werkzeug.utils

import nyaruhodo

DATABASE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db.sqlite3")
server = flask.Flask(__name__)
server.config["FILES"] = os.path.join(os.path.dirname(__file__), "data", "files")
server.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024
server.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
os.makedirs(os.path.join(os.path.dirname(__file__), "data", "files"), exist_ok=True)

def get_database():

    database = getattr(flask.g, "_database", None)

    if database is None:

        database = flask.g._database = sqlite3.connect(DATABASE_FILE)
        database.row_factory = sqlite3.Row

    return database

def active_user():
    """Return the username for the current session, or 'anonymous'."""

    return flask.session.get("username", "anonymous")

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
        database.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, virus_total_key TEXT)")
        database.execute("CREATE TABLE IF NOT EXISTS records (record_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, file_name TEXT NOT NULL, file_type TEXT, status TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users (user_id))")
        database.commit()

def requirelogin(f):

    @functools.wraps(f)

    def decorated_function(*args, **kwargs):

        if "user_id" not in flask.session:

            nyaruhodo.telemetry.warning("anonymous", f"Unauthenticated request to protected route '{flask.request.path}'; redirecting to login.")
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
            cursor = database.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            database.commit()
            flask.session["user_id"]  = cursor.lastrowid
            flask.session["username"] = username
            nyaruhodo.telemetry.info(username, f"Account Created '{username}' ({cursor.lastrowid})")
            return flask.redirect(flask.url_for("dashboard"))

        except sqlite3.IntegrityError:

            nyaruhodo.telemetry.warning("anonymous", f"Registration Failed '{username}'")
            return flask.render_template("register.html", error="Sorry! Username is already taken.")

    return flask.render_template("register.html")

@server.route("/dashboard/login", methods=["GET", "POST"])

def login():

    if flask.request.method == "POST":

        username = flask.request.form["username"]
        password = flask.request.form["password"]
        database = get_database()
        user     = database.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user and werkzeug.security.check_password_hash(user["password"], password):

            flask.session["user_id"]  = user["user_id"]
            flask.session["username"] = user["username"]
            nyaruhodo.telemetry.info(username, f"Account Log In '{username}'")
            return flask.redirect(flask.url_for("dashboard"))

        nyaruhodo.telemetry.warning("anonymous", f"Log In Failed: '{username}'")
        return flask.render_template("login.html", error="Sorry! Username or password is incorrect.")

    return flask.render_template("login.html")

@server.route("/dashboard/logout")

def logout():

    nyaruhodo.telemetry.info(username, f"Account Log Out '{active_user()}'")
    flask.session.clear()

    return flask.redirect(flask.url_for("index"))

@server.route("/dashboard")
@requirelogin

def dashboard():

    database = get_database()
    records  = database.execute("SELECT * FROM records WHERE user_id = ? ORDER BY timestamp DESC", (flask.session["user_id"],)).fetchall()
    user     = database.execute("SELECT * FROM users WHERE user_id = ?", (flask.session["user_id"],)).fetchone()
    nyaruhodo.telemetry.info(active_user(), f"Dashboard Access '{active_user()}'")
    return flask.render_template("dashboard.html", username=flask.session["username"], logs=records, virus_total_key=user["virus_total_key"] or "")

@server.route("/dashboard/scan", methods=["POST"])

def scan():

    user = active_user()

    if "file" not in flask.request.files:

        nyaruhodo.telemetry.error(user, "Scan Failed (No File)")
        return flask.jsonify({"error": "Sorry! No file was uploaded."}), 400

    file = flask.request.files["file"]

    if file.file_name == "":

        nyaruhodo.telemetry.error(user, "Scan Failed (Empty File Name)")
        return flask.jsonify({"error": "Sorry! No file was selected."}), 400

    if file:

        file_name  = werkzeug.utils.secure_file_name(file.file_name)
        file_path  = os.path.join(server.config["UPLOAD_FOLDER"], file_name)
        file.save(file_path)
        nyaruhodo.telemetry.info(user, f"Scan Started '{file_name}'")
        result        = nyaruhodo.core.scan(file_path, file_name)
        detected_type = result.get("file_type")
        metadata      = nyaruhodo.properties.read(file_path, detected_type)

        if metadata:

            result["metadata"] = metadata

        if result["file_type"] == "UNKNOWN":

            nyaruhodo.telemetry.warning(user, f"Scan Completed: '{file_name}' (UNKNOWN)")

        elif result["mismatch"]:

            nyaruhodo.telemetry.warning(user, f"Scan Completed: '{file_name}', ({result.get('extension')}, {detected_type}, MISMATCH)")

        else:

            nyaruhodo.telemetry.info(user, f"Scan Completed: '{file_name}', ({detected_type}, MATCH)")

        if result["mismatch"] and flask.request.form.get("virustotal") == "true":

            key = None

            if "user_id" in flask.session:

                db_user = get_database().execute("SELECT virus_total_key FROM users WHERE user_id = ?", (flask.session["user_id"],)).fetchone()
                key     = db_user["virus_total_key"] if db_user and db_user["virus_total_key"] else None

            if not key:

                key = os.environ.get("VIRUS_TOTAL_API_KEY")

            nyaruhodo.telemetry.info(user, f"VirusTotal '{file_name}'")

            virustotal_result = nyaruhodo.services.virustotal(file_path, key)

            if "error" in virustotal_result:

                nyaruhodo.telemetry.error(user, f"VirusTotal Failed '{file_name}', ({virustotal_result.get('message') or virustotal_result.get('details', 'Unknown Error')})")

            else:

                nyaruhodo.telemetry.info(user, f"VirusTotal Completed '{file_name}', (M={virustotal_result.get('stats_malicious', 0)}, S={virustotal_result.get('stats_suspicious', 0)}, H={virustotal_result.get('stats_harmless', 0)})")

            result["virustotal"] = virustotal_result

        if "user_id" in flask.session:

            database = get_database()

            if result["file_type"] == "UNKNOWN":

                summary = "Unknown"

            elif result["mismatch"]:

                summary = "Mismatch"

            else:

                summary = "Match"

            database.execute("INSERT INTO records (user_id, file_name, file_type, status) VALUES (?, ?, ?, ?)", (flask.session["user_id"], file_name, result["file_type"], summary))
            database.commit()

        return flask.jsonify(result)

    nyaruhodo.telemetry.error(user, "Scan Failed (Unhandled Reason)")
    return flask.jsonify({"error": "Sorry! Processing failed."}), 500

@server.route("/dashboard/delete-account", methods=["POST"])
@requirelogin

def delete_account():

    user     = active_user()
    password = flask.request.form.get("password")
    database = get_database()
    db_user  = database.execute("SELECT * FROM users WHERE user_id = ?", (flask.session["user_id"],)).fetchone()

    if not db_user or not werkzeug.security.check_password_hash(db_user["password"], password):

        nyaruhodo.telemetry.warning(user, f"Account Deletion Failed: '{user}' (Incorrect Password)")
        records = database.execute("SELECT * FROM records WHERE user_id = ? ORDER BY timestamp DESC", (flask.session["user_id"],)).fetchall()
        return flask.render_template("dashboard.html", username=flask.session["username"], logs=records, error="Sorry! Password is incorrect.")

    database.execute("DELETE FROM records WHERE user_id = ?", (flask.session["user_id"],))
    database.execute("DELETE FROM users WHERE user_id = ?", (flask.session["user_id"],))
    database.commit()

    nyaruhodo.telemetry.info(user, f"Account Deleted '{user}'")

    flask.session.clear()
    return flask.redirect(flask.url_for("index"))

@server.route("/dashboard/delete-log/<int:log_id>", methods=["POST"])
@requirelogin

def delete_log(log_id):

    user     = active_user()
    database = get_database()
    entry    = database.execute("SELECT * FROM records WHERE record_id = ? AND user_id = ?", (log_id, flask.session["user_id"])).fetchone()

    if not entry:

        nyaruhodo.telemetry.warning(user, f"Record Delete Failed '{user}', '{log_id}': Entry Not Found or Not Owned by User")
        return flask.redirect(flask.url_for("dashboard"))

    database.execute("DELETE FROM records WHERE record_id = ?", (log_id,))
    database.commit()

    nyaruhodo.telemetry.info(user, f"Record Delete '{user}', '{log_id}' ('{entry['file_name']}')")

    return flask.redirect(flask.url_for("dashboard"))

@server.route("/dashboard/virustotal", methods=["POST"])
@requirelogin

def virustotal():

    user = active_user()
    key  = flask.request.form.get("virustotal_key", "").strip()

    database = get_database()
    database.execute("UPDATE users SET virus_total_key = ? WHERE user_id = ?", (key, flask.session["user_id"]))
    database.commit()

    if key:

        nyaruhodo.telemetry.info(user, f"Account '{user}' Saved VirusTotal API Key")

    else:

        nyaruhodo.telemetry.info(user, f"Account '{user}' Removed VirusTotal API Key")

    return flask.redirect(flask.url_for("dashboard"))

if __name__ == "__main__":

    nyaruhodo.init.paint_screen()
    initialise_database()
    server.run(debug=True, host="0.0.0.0", port=5000)