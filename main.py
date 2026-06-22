
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

    conn.close
    return redirect("/")

@app.route("/")
def index():
    # Wir schauen nach, ob jemand eingeloggt ist (ob ein Name in der Session steckt)
    aktuelle_user = session.get("username")

    if aktuelle_user:
        # Wenn du eingeloggt bist, zeigen wir eine Begrüßung an
        return f"<h1>Hallo {aktuelle_user}! Du bist erfolgreich eingeloggt. 🎉</h1>"

    # Wenn niemand eingeloggt ist, zeigen wir ein einfaches Login-Formular an
    return """
        <h1>Bitte einloggen oder Account erstellen</h1>
        <form action="/login" method="POST">
            <input type="text" name="username" placeholder="Dein Wunschname" required>
            <button type="submit">Loslegen</button>
        </form>
    """


if __name__ == "__main__":
    init_db()  # Erstellt die Tabelle beim Starten
    app.run(debug=True)