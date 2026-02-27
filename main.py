import flask
import functools
import os
import sqlite3
import werkzeug.security
import werkzeug.utils

import nyaruhodo

DATABASE_FILEPATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db.sqlite3")
server = flask.Flask(__name__)
server.config["FILES"] = os.path.join(os.path.dirname(__file__), "data", "files")
server.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024
server.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
os.makedirs(os.path.join(os.path.dirname(__file__), "data", "files"), exist_ok=True)


def GetDatabase():
    databaseresource = getattr(flask.g, "_database", None)
    if databaseresource is None:
        databaseresource = flask.g._database = sqlite3.connect(DATABASE_FILEPATH)
        databaseresource.row_factory = sqlite3.Row
    return databaseresource


@server.route("/favicon.ico")
def Favicon():
    return flask.send_from_directory(os.path.join(server.root_path, "static"), "favicon.png", mimetype="image/png")


@server.teardown_appcontext
def CloseConnection(exceptionrecord):
    databaseresource = getattr(flask.g, "_database", None)
    if databaseresource is not None:
        databaseresource.close()


def InitialiseDatabase():
    with server.app_context():
        databaseresource = GetDatabase()
        databaseresource.execute(
            "CREATE TABLE IF NOT EXISTS users (userid INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, virustotalkey TEXT)"
        )
        databaseresource.execute(
            "CREATE TABLE IF NOT EXISTS records (recordid INTEGER PRIMARY KEY AUTOINCREMENT, userid INTEGER NOT NULL, filename TEXT NOT NULL, filetype TEXT, status TEXT, createdat DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (userid) REFERENCES users (userid))"
        )
        databaseresource.commit()


def RequireSignIn(authfunction):
    @functools.wraps(authfunction)
    def DecoratedFunction(*arguments, **keywordarguments):
        if "userid" not in flask.session:
            nyaruhodo.telemetry.Warning("anonymous", f"Unauthenticated request '{flask.request.path}'")
            return flask.redirect(flask.url_for("SignIn"))
        return authfunction(*arguments, **keywordarguments)

    return DecoratedFunction


@server.route("/")
def Index():
    return flask.render_template("index.html", userid=flask.session.get("userid"))


@server.route("/dashboard/register", methods=["GET", "POST"])
def Register():
    if flask.request.method == "POST":
        username = flask.request.form["username"]
        password = flask.request.form["password"]
        databaseresource = GetDatabase()
        try:
            hashedpassword = werkzeug.security.generate_password_hash(password)
            cursorrecord = databaseresource.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)", (username, hashedpassword)
            )
            databaseresource.commit()
            flask.session["userid"] = cursorrecord.lastrowid
            flask.session["username"] = username
            nyaruhodo.telemetry.Info(username, f"Account created '{username}' ({cursorrecord.lastrowid})")
            return flask.redirect(flask.url_for("Dashboard"))
        except sqlite3.IntegrityError:
            nyaruhodo.telemetry.Warning("anonymous", f"Registration failed '{username}'")
            return flask.render_template("register.html", ErrorMessage="Registration failed. The username you entered is already in use.")
    return flask.render_template("register.html")


@server.route("/dashboard/signin", methods=["GET", "POST"])
def SignIn():
    if flask.request.method == "POST":
        username = flask.request.form["username"]
        password = flask.request.form["password"]
        databaseresource = GetDatabase()
        userrecord = databaseresource.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if userrecord and werkzeug.security.check_password_hash(userrecord["password"], password):
            flask.session["userid"] = userrecord["userid"]
            flask.session["username"] = userrecord["username"]
            nyaruhodo.telemetry.Info(username, f"Account sign in '{username}'")
            return flask.redirect(flask.url_for("Dashboard"))

        nyaruhodo.telemetry.Warning("anonymous", f"Sign in failed '{username}'")
        return flask.render_template("signin.html", ErrorMessage="Authentication failed. The username or password you entered is incorrect.")
    return flask.render_template("signin.html")


@server.route("/dashboard/signout")
def SignOut():
    sessionusername = flask.session.get("username", "anonymous")
    nyaruhodo.telemetry.Info(sessionusername, f"Account sign out '{sessionusername}'")
    flask.session.clear()
    return flask.redirect(flask.url_for("Index"))


@server.route("/dashboard")
@RequireSignIn
def Dashboard():
    databaseresource = GetDatabase()
    entries = databaseresource.execute(
        "SELECT * FROM records WHERE userid = ? ORDER BY createdat DESC", (flask.session["userid"],)
    ).fetchall()
    userrecord = databaseresource.execute("SELECT * FROM users WHERE userid = ?", (flask.session["userid"],)).fetchone()
    nyaruhodo.telemetry.Info(flask.session.get("username", "anonymous"), "Dashboard access")
    return flask.render_template(
        "dashboard.html",
        username=flask.session["username"],
        entries=entries,
        virustotalkey=userrecord["virustotalkey"] or "",
    )


@server.route("/dashboard/analyse", methods=["POST"])
def AnalyseFile():
    username = flask.session.get("username", "anonymous")
    if "file" not in flask.request.files:
        nyaruhodo.telemetry.Error(username, "Analysis failed (no file)")
        return flask.jsonify({"error": "The request did not include a file. Please select a file before submitting."}), 400

    uploadedfile = flask.request.files["file"]
    if uploadedfile.filename == "":
        nyaruhodo.telemetry.Error(username, "Analysis failed (empty filename)")
        return flask.jsonify({"error": "No file was selected. Please choose a file and try again."}), 400

    filename = werkzeug.utils.secure_filename(uploadedfile.filename)
    filepath = os.path.join(server.config["FILES"], filename)
    uploadedfile.save(filepath)

    nyaruhodo.telemetry.Info(username, f"Analysis started '{filename}'")
    analyserecord = nyaruhodo.core.AnalyseFile(filepath, filename)
    detectedfiletype = analyserecord.get("file_type")
    metadatarecord = nyaruhodo.properties.Read(filepath, detectedfiletype)
    if metadatarecord:
        analyserecord["metadata"] = metadatarecord

    if analyserecord["mismatch"] and flask.request.form.get("virustotal") == "true":
        userkey = None
        if "userid" in flask.session:
            userrow = GetDatabase().execute("SELECT virustotalkey FROM users WHERE userid = ?", (flask.session["userid"],)).fetchone()
            userkey = userrow["virustotalkey"] if userrow and userrow["virustotalkey"] else None
        if not userkey:
            userkey = os.environ.get("VIRUSTOTAL_API_KEY")
        analyserecord["virustotal"] = nyaruhodo.services.VirusTotalLookup(filepath, userkey)

    if "userid" in flask.session:
        statusvalue = "Unknown" if analyserecord["file_type"] == "UNKNOWN" else ("Mismatch" if analyserecord["mismatch"] else "Match")
        databaseresource = GetDatabase()
        databaseresource.execute(
            "INSERT INTO records (userid, filename, filetype, status) VALUES (?, ?, ?, ?)",
            (flask.session["userid"], filename, analyserecord["file_type"], statusvalue),
        )
        databaseresource.commit()

    return flask.jsonify(analyserecord)


@server.route("/dashboard/delete-account", methods=["POST"])
@RequireSignIn
def DeleteAccount():
    username = flask.session.get("username", "anonymous")
    password = flask.request.form.get("password")
    databaseresource = GetDatabase()
    userrecord = databaseresource.execute("SELECT * FROM users WHERE userid = ?", (flask.session["userid"],)).fetchone()

    if not userrecord or not werkzeug.security.check_password_hash(userrecord["password"], password):
        entries = databaseresource.execute(
            "SELECT * FROM records WHERE userid = ? ORDER BY createdat DESC", (flask.session["userid"],)
        ).fetchall()
        return flask.render_template(
            "dashboard.html", username=flask.session["username"], entries=entries, ErrorMessage="Account deletion failed. The password you entered is incorrect."
        )

    databaseresource.execute("DELETE FROM records WHERE userid = ?", (flask.session["userid"],))
    databaseresource.execute("DELETE FROM users WHERE userid = ?", (flask.session["userid"],))
    databaseresource.commit()
    nyaruhodo.telemetry.Info(username, f"Account deleted '{username}'")
    flask.session.clear()
    return flask.redirect(flask.url_for("Index"))


@server.route("/dashboard/delete-entry/<int:recordid>", methods=["POST"])
@RequireSignIn
def DeleteRecord(recordid):
    databaseresource = GetDatabase()
    entryrecord = databaseresource.execute(
        "SELECT * FROM records WHERE recordid = ? AND userid = ?", (recordid, flask.session["userid"])
    ).fetchone()
    if not entryrecord:
        return flask.redirect(flask.url_for("Dashboard"))

    databaseresource.execute("DELETE FROM records WHERE recordid = ?", (recordid,))
    databaseresource.commit()
    return flask.redirect(flask.url_for("Dashboard"))


@server.route("/dashboard/virustotal", methods=["POST"])
@RequireSignIn
def VirusTotal():
    virustotalkey = flask.request.form.get("virustotalkey", "").strip()
    databaseresource = GetDatabase()
    databaseresource.execute("UPDATE users SET virustotalkey = ? WHERE userid = ?", (virustotalkey, flask.session["userid"]))
    databaseresource.commit()
    return flask.redirect(flask.url_for("Dashboard"))


if __name__ == "__main__":
    nyaruhodo.init.PaintScreen()
    InitialiseDatabase()
    server.run(debug=True, host="0.0.0.0", port=5000)
