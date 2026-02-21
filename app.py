from flask import Flask, render_template, request, redirect, jsonify
from datetime import datetime
import sqlite3

app = Flask(__name__)
ADMIN_PASSWORD = "collumanish89"
# Create database
def init_db():
    conn = sqlite3.connect("messages.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            message TEXT,
            time TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/send", methods=["POST"])
def send():
    name = request.form["name"].strip()
    message = request.form["message"].strip()

    if not name or not message:
        return "", 400

    conn = sqlite3.connect("messages.db")
    c = conn.cursor()

    # 🔥 Anti-spam: check last message time from this name
    c.execute("SELECT time FROM messages WHERE name=? ORDER BY id DESC LIMIT 1", (name,))
    last = c.fetchone()

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    if last:
        last_time = datetime.strptime(last[0], "%H:%M:%S")
        diff = (now - last_time).total_seconds()
        if diff < 3:
            conn.close()
            return "", 429  # Too many requests

    # Insert message
    c.execute("INSERT INTO messages (name, message, time) VALUES (?, ?, ?)",
              (name, message, current_time))
    conn.commit()

    # 🔥 Keep only last 100 messages
    c.execute("""
        DELETE FROM messages 
        WHERE id NOT IN (
            SELECT id FROM messages ORDER BY id DESC LIMIT 100
        )
    """)
    conn.commit()

    conn.close()
    return "", 204

@app.route("/admin")
def admin():
    password = request.args.get("password")

    if password != ADMIN_PASSWORD:
        return "Unauthorized", 403

    conn = sqlite3.connect("messages.db")
    c = conn.cursor()
    c.execute("SELECT name, message, time FROM messages ORDER BY id DESC")
    messages = c.fetchall()
    conn.close()
    return render_template("admin.html", messages=messages)

@app.route("/clear", methods=["POST"])
def clear_chat():
    try:
        password = request.form.get("password")

        if password != ADMIN_PASSWORD:
            return "Unauthorized", 403

        conn = sqlite3.connect("messages.db")
        c = conn.cursor()
        c.execute("DELETE FROM messages")
        conn.commit()
        conn.close()

        return "", 204

    except Exception as e:
        print("ERROR:", e)
        return "Server Error", 500

@app.route("/get_messages")
def get_messages():
    conn = sqlite3.connect("messages.db")
    c = conn.cursor()
    c.execute("SELECT name, message, time FROM messages ORDER BY id DESC")
    messages = c.fetchall()
    conn.close()
    return jsonify(messages)

if __name__ == "__main__":
    app.run()
    
