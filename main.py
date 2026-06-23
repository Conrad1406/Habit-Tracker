
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
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://googleapis.com" rel="stylesheet">
        <style>
            body {
                background-color: #121214;
                color: white;
                font-family: 'Montserrat', sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
            }
            h1 { font-weight: 700; margin-bottom: 20px; }
            .login-box {
                background-color: #1a1a1e;
                padding: 30px;
                border-radius: 16px;
                border: 1px solid #29292e;
                display: flex;
                flex-direction: column;
                gap: 15px;
                width: 300px;
                box-sizing: border-box;
            }
            input {
                background: #121214;
                border: 1px solid #29292e;
                color: white;
                padding: 12px;
                border-radius: 8px;
                font-family: 'Montserrat';
                font-size: 16px;
            }
            button {
                background: white;
                color: black;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                font-family: 'Montserrat';
                font-size: 16px;
            }
        </style>
    </head>
    <body>
        <h1>habit tracker</h1>
        <div class="login-box">
            <h2 style="margin: 0; font-size: 16px; font-weight: 600; color: #a8a8b3;">bitte einloggen</h2>
            <form action="/login" method="POST" style="display: flex; flex-direction: column; gap: 15px;">
                <input type="text" name="username" placeholder="benutzername" required>
                <button type="submit">go</button>
            </form>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    init_db()
    app.run(debug=True)