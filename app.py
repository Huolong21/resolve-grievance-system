

from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Connect to the database
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# Create the complaints table
def create_table():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT UNIQUE,
            name TEXT,
            email TEXT,
            category TEXT,
            subject TEXT,
            description TEXT,
            status TEXT DEFAULT 'Pending',
            date TEXT,
            updated TEXT
        )
    """)
    conn.commit()
    conn.close()


# Home page
@app.route("/")
def home():
    return render_template("home.html")


# Submit a complaint
@app.route("/submit", methods=["GET", "POST"])
def submit():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        category = request.form["category"]
        subject = request.form["subject"]
        description = request.form["description"]

        conn = get_db_connection()

        next_number = conn.execute(
            "SELECT COUNT(*) FROM complaints"
        ).fetchone()[0] + 1

        complaint_id = f"G{next_number:04d}"
        today = datetime.now().strftime("%d-%m-%Y")

        conn.execute("""
            INSERT INTO complaints
            (complaint_id, name, email, category, subject,
             description, status, date, updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            complaint_id, name, email, category, subject,
            description, "Pending", today, today
        ))

        conn.commit()
        conn.close()

        return f"Complaint submitted successfully! Your Complaint ID is {complaint_id}"

    return render_template("submit.html")


# Track a complaint
@app.route("/track", methods=["GET", "POST"])
def track():
    complaint = None
    message = ""

    if request.method == "POST":
        complaint_id = request.form["complaint_id"].strip()

        conn = get_db_connection()
        complaint = conn.execute(
            "SELECT * FROM complaints WHERE complaint_id = ?",
            (complaint_id,)
        ).fetchone()
        conn.close()

        if complaint is None:
            message = "No complaint found. Please check your ID."

    return render_template("track.html", complaint=complaint, message=message)


# Admin dashboard
@app.route("/admin")
def admin():
    conn = get_db_connection()

    complaints = conn.execute(
        "SELECT * FROM complaints ORDER BY id DESC"
    ).fetchall()

    total = len(complaints)
    pending = sum(c["status"] == "Pending" for c in complaints)
    progress = sum(c["status"] == "In Progress" for c in complaints)
    resolved = sum(c["status"] == "Resolved" for c in complaints)

    conn.close()

    return render_template(
        "admin.html",
        complaints=complaints,
        total=total,
        pending=pending,
        progress=progress,
        resolved=resolved
    )


# Update complaint status
@app.route("/update/<int:complaint_number>", methods=["POST"])
def update(complaint_number):
    new_status = request.form["status"]

    conn = get_db_connection()
    conn.execute(
        "UPDATE complaints SET status = ?, updated = ? WHERE id = ?",
        (new_status, datetime.now().strftime("%d-%m-%Y"), complaint_number)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


create_table()

if __name__ == "__main__":
    app.run(debug=True)