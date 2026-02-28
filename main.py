import flask
import functools
import os
import sqlite3
import uuid
import werkzeug.security
import werkzeug.utils

import nyaruhodo

server                              = flask.Flask(__name__)
server.config["FILES"]              = os.path.join(os.path.dirname(__file__), "data", "files")
server.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024
server.secret_key                   = os.environ.get("SECRET_KEY") or os.urandom(24)

def GetDatabase():

    database = getattr(flask.g, "_database", None)

    if database is None:

        database             = flask.g._database = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), "db.sqlite3"))
        database.row_factory = sqlite3.Row

    return database

@server.route("/favicon.ico")
def Favicon():

    return flask.send_from_directory(os.path.join(server.rootpath, "static"), "favicon.png", mimetype = "image/png")

@server.teardown_appcontext
def CloseConnection(exceptionrecord):

    database = getattr(flask.g, "_database", None)

    if database is not None:

        database.close()

def InitialiseDatabase():

    with server.app_context():

        os.makedirs(server.config["FILES"], exist_ok=True)
        database = GetDatabase()
        database.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL COLLATE NOCASE, display_name TEXT NOT NULL, password TEXT NOT NULL, virustotal_api_key TEXT, priviledge INTEGER DEFAULT 0)")
        database.execute("CREATE TABLE IF NOT EXISTS records (record_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, filename TEXT NOT NULL, filetype TEXT, status TEXT, created DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users (user_id))")
        database.execute("CREATE TABLE IF NOT EXISTS events (event_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, filename TEXT, outcome TEXT NOT NULL, created DATETIME DEFAULT CURRENT_TIMESTAMP)")
        database.commit()

def RequireSignIn(authfunction):

    @functools.wraps(authfunction)
    def DecoratedFunction(*arguments, **keywordarguments):

        if "user_id" not in flask.session:

            nyaruhodo.telemetry.Warn("anonymous", f"Unauthenticated request '{flask.request.path}'")

            return flask.redirect(flask.url_for("SignIn"))

        return authfunction(*arguments, **keywordarguments)

    return DecoratedFunction

def RequireAdmin(adminfunction):

    @functools.wraps(adminfunction)
    def DecoratedFunction(*arguments, **keywordarguments):

        if "user_id" not in flask.session:

            nyaruhodo.telemetry.Warn("anonymous", f"Unauthenticated admin request '{flask.request.path}'")

            return flask.redirect(flask.url_for("SignIn"))

        if not flask.session.get("priviledge"):

            nyaruhodo.telemetry.Warn(flask.session.get("username", "anonymous"), f"Unauthorised admin request '{flask.request.path}'")

            return flask.abort(403)

        return adminfunction(*arguments, **keywordarguments)

    return DecoratedFunction

@server.route("/")
def Index():

    return flask.render_template("index.html", user_id = flask.session.get("user_id"))

@server.route("/create-account", methods = ["GET", "POST"])
def CreateAccount():

    if flask.request.method == "POST":

        username     = flask.request.form["username"].strip()
        display_name = flask.request.form["display_name"].strip()
        password     = flask.request.form["password"]
        database     = GetDatabase()

        if not username:

            return flask.render_template("create-account.html", message = "Account creation failed. A username is required.")

        if not display_name:

            return flask.render_template("create-account.html", message = "Account creation failed. A display name is required.")

        try:

            admin_users                   = database.execute("SELECT COUNT(*) FROM users WHERE priviledge = 1").fetchone()[0]
            primary_admin                 = (admin_users == 0)
            password                      = werkzeug.security.generate_password_hash(password)
            cursor                        = database.execute("INSERT INTO users (username, display_name, password, priviledge) VALUES (?, ?, ?, ?)", (username, display_name, hashed_password, 1 if primary_admin else 0))
            database.commit()
            flask.session["user_id"]      = cursor.lastrowid
            flask.session["username"]     = username
            flask.session["display_name"] = display_name
            flask.session["priviledge"]   = primary_admin
            nyaruhodo.telemetry.Info(username, f"Account created '{username}' (display: '{display_name}') ({cursor.lastrowid}){' [admin]' if primary_admin else ''}")

            if primary_admin:

                return flask.redirect(flask.url_for("AdminDashboard"))

            return flask.redirect(flask.url_for("Dashboard"))

        except sqlite3.IntegrityError:

            nyaruhodo.telemetry.Warn("anonymous", f"Account creation failed '{username}'")

            return flask.render_template("create-account.html", message = "Account creation failed. That username is already in use.")

    return flask.render_template("create-account.html")

@server.route("/sign-in", methods = ["GET", "POST"])
def SignIn():

    if flask.request.method == "POST":

        username = flask.request.form["username"].strip()
        password = flask.request.form["password"]
        database = GetDatabase()
        userdata = database.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if userdata and werkzeug.security.check_password_hash(userdata["password"], password):

            flask.session["user_id"]      = userdata["user_id"]
            flask.session["username"]     = userdata["username"]
            flask.session["display_name"] = userdata["display_name"]
            flask.session["priviledge"]   = bool(userdata["priviledge"])
            nyaruhodo.telemetry.Info(username, f"Account sign in '{username}'")

            if userdata["priviledge"]:

                return flask.redirect(flask.url_for("AdminDashboard"))

            return flask.redirect(flask.url_for("Dashboard"))

        nyaruhodo.telemetry.Warn("anonymous", f"Sign in failed '{username}'")

        return flask.render_template("sign-in.html", message = "Authentication failed. The username or password you entered is incorrect.")

    return flask.render_template("sign-in.html")

@server.route("/sign-out")
def SignOut():

    username = flask.session.get("username", "anonymous")
    nyaruhodo.telemetry.Info(username, f"Account sign out '{username}'")
    flask.session.clear()

    return flask.redirect(flask.url_for("Index"))

@server.route("/analyse", methods = ["POST"])
def AnalyseFile():

    username = flask.session.get("username", "anonymous")
    user_id  = flask.session.get("user_id")
    database = GetDatabase()

    if "file" not in flask.request.files:

        database.execute("INSERT INTO events (user_id, filename, outcome) VALUES (?, ?, ?)", (user_id, "", "failed"))
        database.commit()
        nyaruhodo.telemetry.Error(username, "Analysis failed (no file)")

        return flask.jsonify({"error": "The request did not include a file. Please select a file before submitting."}), 400

    file = flask.request.files["file"]

    if file.filename == "":

        database.execute("INSERT INTO events (user_id, filename, outcome) VALUES (?, ?, ?)", (user_id, "", "failed"))
        database.commit()
        nyaruhodo.telemetry.Error(username, "Analysis failed (empty filename)")

        return flask.jsonify({"error": "No file was selected. Please choose a file and try again."}), 400

    filename = werkzeug.utils.secure_filename(file.filename)

    if not filename:

        database.execute("INSERT INTO events (user_id, filename, outcome) VALUES (?, ?, ?)", (user_id, file.filename or "", "failed"))
        database.commit()

        return flask.jsonify({"error": "The filename contains no valid characters."}), 400

    unique_filename   = f"{uuid.uuid4().hex}_{filename}"
    filepath          = os.path.join(server.config["FILES"], unique_filename)
    file.save(filepath)
    nyaruhodo.telemetry.Info(username, f"Analysis started '{filename}'")
    analysis          = nyaruhodo.core.AnalyseFile(filepath, filename)
    detected_filetype = analysis.get("detected_filetype")
    metadata          = nyaruhodo.properties.Read(filepath, detected_filetype)

    if metadata:

        analysis["metadata"] = metadata

    if flask.request.form.get("virustotal") == "true":

        virustotal_api_key = None

        if "user_id" in flask.session:

            userdata           = database.execute("SELECT virustotal_api_key FROM users WHERE user_id = ?", (flask.session["user_id"],)).fetchone()
            virustotal_api_key = userdata["virustotal_api_key"] if userdata and userdata["virustotal_api_key"] else None

        if not virustotal_api_key:

            virustotal_api_key = os.environ.get("VIRUSTOTAL_API_KEY")

        analysis["virustotal"] = nyaruhodo.services.VirusTotalLookup(filepath, virustotal_api_key)

    if "user_id" in flask.session:

        file_status = "Unknown" if analysis["detected_filetype"] == "UNKNOWN" else ("Mismatch" if analysis["mismatch"] else "Match")
        database.execute("INSERT INTO records (user_id, filename, filetype, status) VALUES (?, ?, ?, ?)", (flask.session["user_id"], filename, analysis["detected_filetype"], file_status))
        database.commit()

    database.execute("INSERT INTO events (user_id, filename, outcome) VALUES (?, ?, ?)", (user_id, filename, "completed"))
    database.commit()

    return flask.jsonify(analysis)

@server.route("/dashboard")
@RequireSignIn
def Dashboard():

    database     = GetDatabase()
    entries      = database.execute("SELECT * FROM records WHERE user_id = ? ORDER BY created DESC", (flask.session["user_id"],)).fetchall()
    userdata     = database.execute("SELECT * FROM users WHERE user_id = ?", (flask.session["user_id"],)).fetchone()
    display_name = flask.session.get("display_name", flask.session.get("username", ""))
    nyaruhodo.telemetry.Info(flask.session.get("username", "anonymous"), "Dashboard access")

    return flask.render_template("dashboard.html", display_name = display_name, entries = entries, virustotal_api_key = userdata["virustotal_api_key"] or "")

@server.route("/dashboard/delete-account", methods = ["POST"])
@RequireSignIn
def DeleteAccount():

    username     = flask.session.get("username", "anonymous")
    display_name = flask.session.get("display_name", username)
    password     = flask.request.form.get("password")
    database     = GetDatabase()
    userdata     = database.execute("SELECT * FROM users WHERE user_id = ?", (flask.session["user_id"],)).fetchone()

    if not userdata or not werkzeug.security.check_password_hash(userdata["password"], password):

        entries = database.execute("SELECT * FROM records WHERE user_id = ? ORDER BY created DESC", (flask.session["user_id"],)).fetchall()

        return flask.render_template("dashboard.html", display_name = display_name, entries = entries, virustotal_api_key = userdata["virustotal_api_key"] if userdata and userdata["virustotal_api_key"] else "", message = "Account deletion failed. The password you entered is incorrect.")

    database.execute("DELETE FROM records WHERE user_id = ?", (flask.session["user_id"],))
    database.execute("DELETE FROM users WHERE user_id = ?", (flask.session["user_id"],))
    database.commit()
    nyaruhodo.telemetry.Info(username, f"Account deleted '{username}'")
    flask.session.clear()

    return flask.redirect(flask.url_for("Index"))

@server.route("/dashboard/delete-entry/<int:record_id>", methods = ["POST"])
@RequireSignIn
def DeleteRecord(record_id):

    database = GetDatabase()
    entry    = database.execute("SELECT * FROM records WHERE record_id = ? AND user_id = ?", (record_id, flask.session["user_id"])).fetchone()

    if not entry:

        return flask.redirect(flask.url_for("Dashboard"))

    database.execute("DELETE FROM records WHERE record_id = ?", (record_id,))
    database.commit()

    return flask.redirect(flask.url_for("Dashboard"))

@server.route("/dashboard/virustotal", methods = ["POST"])
@RequireSignIn
def VirusTotal():

    virustotal_api_key = flask.request.form.get("virustotal_api_key", "").strip()
    database           = GetDatabase()
    database.execute("UPDATE users SET virustotal_api_key = ? WHERE user_id = ?", (virustotal_api_key, flask.session["user_id"]))
    database.commit()

    return flask.redirect(flask.url_for("Dashboard"))

@server.route("/dashboard/admin")
@RequireAdmin
def AdminDashboard():

    database     = GetDatabase()
    normal_users = database.execute("SELECT COUNT(*) FROM users WHERE priviledge = 0").fetchone()[0]
    admin_users  = database.execute("SELECT COUNT(*) FROM users WHERE priviledge = 1").fetchone()[0]
    events       = database.execute("SELECT outcome, COUNT(*) AS cnt FROM events GROUP BY outcome").fetchall()
    event_data   = {event["outcome"]: event["cnt"] for event in events}
    records      = database.execute("SELECT status, COUNT(*) AS cnt FROM records GROUP BY status").fetchall()
    record_data  = {record["status"]: record["cnt"] for record in records}
    users        = database.execute("SELECT u.user_id, u.username, u.display_name, u.priviledge, COUNT(r.record_id) AS file_count, COALESCE(SUM(CASE WHEN r.status = 'Mismatch' THEN 1 ELSE 0 END), 0) AS mismatch_count, COALESCE(SUM(CASE WHEN r.status = 'Unknown' THEN 1 ELSE 0 END), 0) AS unknown_count, MAX(r.created) AS last_scan FROM users u LEFT JOIN records r ON u.user_id = r.user_id GROUP BY u.user_id ORDER BY u.username COLLATE NOCASE").fetchall()
    user_records = {}

    for user in users:

        user_records[user["user_id"]] = database.execute("SELECT * FROM records WHERE user_id = ? ORDER BY created DESC", (user["user_id"],)).fetchall()

    scans           = event_data.get("completed", 0) + event_data.get("failed", 0)
    scans_completed = event_data.get("completed", 0)
    scans_failed    = event_data.get("failed", 0)
    display_name    = flask.session.get("display_name", flask.session.get("username", ""))
    nyaruhodo.telemetry.Info(flask.session.get("username", "anonymous"), "Admin dashboard access")

    return flask.render_template("admin-dashboard.html", display_name = display_name, normal_users = normal_users, admin_users = admin_users, scans = scans, scans_completed = scans_completed, scans_failed = scans_failed, record_data = record_data, users = users, user_records = user_records, current_user_id = flask.session["user_id"])

@server.route("/dashboard/admin/toggle-admin/<int:user_id>", methods = ["POST"])
@RequireAdmin
def AdminToggleAdmin(user_id):

    if user_id == flask.session["user_id"]:

        return flask.redirect(flask.url_for("AdminDashboard"))

    database = GetDatabase()
    userdata = database.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()

    if not userdata:

        return flask.redirect(flask.url_for("AdminDashboard"))

    priviledge = 0 if userdata["priviledge"] else 1
    database.execute("UPDATE users SET priviledge = ? WHERE user_id = ?", (priviledge, user_id))
    database.commit()
    nyaruhodo.telemetry.Info(flask.session.get("username", "anonymous"), f"Admin {'granted to' if priviledge else 'revoked from'} '{userdata['username']}'")

    return flask.redirect(flask.url_for("AdminDashboard"))

@server.route("/dashboard/admin/delete-user/<int:user_id>", methods = ["POST"])
@RequireAdmin
def AdminDeleteUser(user_id):

    if user_id == flask.session["user_id"]:

        return flask.redirect(flask.url_for("AdminDashboard"))

    database = GetDatabase()
    userdata = database.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()

    if not userdata:

        return flask.redirect(flask.url_for("AdminDashboard"))

    database.execute("DELETE FROM records WHERE user_id = ?", (user_id,))
    database.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    database.commit()
    nyaruhodo.telemetry.Info(flask.session.get("username", "anonymous"), f"User deleted '{userdata['username']}' by admin")

    return flask.redirect(flask.url_for("AdminDashboard"))

@server.route("/admin/delete-events", methods = ["POST"])
@RequireAdmin
def AdminDeleteEvents():

    database = GetDatabase()
    database.execute("DELETE FROM events")
    database.commit()
    nyaruhodo.telemetry.Info(flask.session.get("username", "anonymous"), "Event log cleared by admin")

    return flask.redirect(flask.url_for("AdminDashboard"))

if __name__ == "__main__":

    nyaruhodo.init.PaintScreen()
    InitialiseDatabase()
    server.run(debug = True, host = "0.0.0.0", port = 5000)