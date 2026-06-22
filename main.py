
from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
from config import secret_key

app = Flask(__name__)
app.secret_key = secret_key

def init_db():
    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS eintraege (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inhalt TEXT NOT NULL,
            typ TEXT NOT NULL, -- 'todo' oder 'notiz'
            user_id INTEGER NOT NULL,
            erledigt INTEGER DEFAULT 0
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS gym_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uebung TEXT NOT NULL,
            gewicht REAL NOT NULL,
            wiederholungen INTEGER NOT NULL,
            datum TEXT NOT NULL,
            user_id INTEGER NOT NULL
        )
    """
    )

    conn.commit()
    conn.close()

@app.route("/login", methods=["POST"])
def login():
    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()

    username = request.form.get("username")

    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if user is not None:
        user_id = user[0]
    else:
        cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
        conn.commit()
        user_id = cursor.lastrowid

    session["user_id"] = user_id
    session["username"] = username

    conn.close()
    return redirect("/")

@app.route("/add", methods=["POST"])
def add():

    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()

    aktuelle_user_id = session.get("user_id")

    typ = request.form.get("typ")
    inhalt = request.form.get("inhalt")
    uebung = request.form.get("uebung")
    gewicht = request.form.get("gewicht")
    wiederholungen = request.form.get("wiederholungen")
    datum = request.form.get("datum")

    if typ == 'gym':
        cursor.execute(
            "INSERT INTO gym_stats (uebung, gewicht, wiederholungen, datum, user_id) VALUES (?, ?, ?, ?, ?)",
            (uebung, gewicht, wiederholungen, datum, aktuelle_user_id),
        )
    else:
        cursor.execute(
            "INSERT INTO eintraege (inhalt, typ, user_id) VALUES (?, ?, ?)",
            (inhalt, typ, aktuelle_user_id),
        )

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/toggle/<int:todo_id>")
def abhaken(todo_id):
    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()

    cursor.execute("SELECT erledigt FROM eintraege WHERE id = ?", (todo_id,))
    ergebnis = cursor.fetchone()

    if ergebnis is not None:
        aktueller_status = ergebnis[0]
        neuer_status = 1 if aktueller_status == 0 else 0

    cursor.execute(
            "UPDATE eintraege SET erledigt = ? WHERE id = ?", 
            (neuer_status, todo_id)
    )    

    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/")
def index():
    aktuelle_user = session.get("username")
    aktuelle_user_id = session.get("user_id")

    if aktuelle_user:
        conn = sqlite3.connect("tracker.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, inhalt, erledigt FROM eintraege WHERE typ='todo' AND user_id = ?", 
            (aktuelle_user_id,)
        )
        alle_todos = cursor.fetchall()
        conn.close()

        gesamt_anzahl = len(alle_todos)
        erledigte_anzahl = sum(1 for todo in alle_todos if todo[2] == 1)

        if gesamt_anzahl > 0:
            prozent = int((erledigte_anzahl / gesamt_anzahl) * 100)
        else:
            prozent = 0

        return render_template("index.html", username=aktuelle_user, todos=alle_todos, fortschritt=prozent)

    return """
        <h1>bitte einloggen oder account erstellen</h1>
        <form action="/login" method="POST">
            <input type="text" name="username" placeholder="benutzername" required>
            <button type="submit">go</button>
        </form>
    """


if __name__ == "__main__":
    init_db()
    app.run(debug=True)