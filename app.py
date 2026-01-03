from flask import Flask, request
from zoneinfo import ZoneInfo
from datetime import datetime
from urllib.parse import unquote
import psycopg2
import os

app = Flask(__name__)

# Supabase connection string from Render Environment Variables
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def valid_timezone(tz):
    try:
        ZoneInfo(tz)
        return True
    except:
        return False


@app.route("/")
def home():
    return "Timezone bot running"


@app.route("/set-timezone")
def set_timezone():
    user = request.args.get("user", "").lower()
    tz = unquote(request.args.get("tz", "")).strip()

    if not user or not tz:
        return "Usage: !tzset Europe/London"

    if not valid_timezone(tz):
        return f"{user}, invalid timezone. Example: Europe/London or America/New_York"

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO timezones (username, timezone)
                VALUES (%s, %s)
                ON CONFLICT (username)
                DO UPDATE SET timezone = EXCLUDED.timezone
                """,
                (user, tz)
            )

    return f"{user}, your timezone ({tz}) has been saved ✅"


@app.route("/get-timezone")
def get_timezone():
    user = request.args.get("user", "").lower()

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT timezone FROM timezones WHERE username = %s",
                (user,)
            )
            row = cur.fetchone()

    if not row:
        return f"{user} has not set a timezone."

    tz = row[0]
    now = datetime.now(ZoneInfo(tz)).strftime("%I:%M %p")

    return f"The local time for {user} ({tz}) is {now} ⏰"


@app.route("/clear-timezone")
def clear_timezone():
    user = request.args.get("user", "").lower()

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM timezones WHERE username = %s",
                (user,)
            )

    return f"{user}, your timezone has been cleared 🗑️"


@app.route("/timezone-all")
def timezone_all():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT username, timezone FROM timezones ORDER BY username"
            )
            rows = cur.fetchall()

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
