from flask import Flask, request
from zoneinfo import ZoneInfo
from datetime import datetime
import sqlite3

app = Flask(__name__)
DB = "database.db"

def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS timezones (
            username TEXT PRIMARY KEY,
            timezone TEXT
        )
        """)

init_db()

def valid_timezone(tz):
    try:
        ZoneInfo(tz)
        return True
    except:
        return False

@app.route("/set-timezone")
def set_timezone():
    user = request.args.get("user", "").lower()
    tz = request.args.get("tz", "")

    if not user or not tz:
        return "Usage: !timezoneset Europe/London"

    if not valid_timezone(tz):
        return f"{user}, invalid timezone. Use Europe/London format."

    with sqlite3.connect(DB) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO timezones (username, timezone) VALUES (?, ?)",
            (user, tz)
        )

    return f"{user}, your timezone ({tz}) has been saved ✅"

@app.route("/get-timezone")
def get_timezone():
    user = request.args.get("user", "").lower()

    with sqlite3.connect(DB) as conn:
        row = conn.execute(
            "SELECT timezone FROM timezones WHERE username = ?",
            (user,)
        ).fetchone()

    if not row:
        return f"{user} has not set a timezone."

    tz = row[0]
    now = datetime.now(ZoneInfo(tz)).strftime("%I:%M %p")

    return f"The local time for {user} ({tz}) is {now} ⏰"

@app.route("/clear-timezone")
def clear_timezone():
    user = request.args.get("user", "").lower()

    with sqlite3.connect(DB) as conn:
        conn.execute("DELETE FROM timezones WHERE username = ?", (user,))

    return f"{user}, your timezone has been cleared 🗑️"

@app.route("/")
def home():
    return "Timezone bot running"

import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

@app.route("/timezone-all")
def timezone_all():
    with sqlite3.connect(DB) as conn:
        rows = conn.execute(
            "SELECT username, timezone FROM timezones ORDER BY username ASC"
        ).fetchall()

    if not rows:
        return "No users have set a timezone yet."

    output = []
    for user, tz in rows:
        try:
            now = datetime.now(ZoneInfo(tz)).strftime("%H:%M")
            output.append(f"{user}: {tz} ({now})")
        except:
            output.append(f"{user}: {tz}")

    return " | ".join(output)
