from flask import Flask, render_template, request
import sqlite3, smtplib, os
from email.message import EmailMessage
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from datetime import datetime
import atexit

# ---------------- Setup ----------------
app = Flask(__name__)
load_dotenv()   # loads your .env email settings

# ---------------- Home Page ----------------
@app.route('/')
def home():
    conn = sqlite3.connect('medicine.db')
    c = conn.cursor()
    c.execute("SELECT * FROM reminders")
    rows = c.fetchall()
    conn.close()
    return render_template('home.html', rows=rows)

# ---------------- Add Reminder ----------------
@app.route('/add', methods=['POST'])
def add():
    name = request.form['name']
    email = request.form['email']
    time = request.form['time']
    conn = sqlite3.connect('medicine.db')
    c = conn.cursor()
    c.execute("INSERT INTO reminders (name, time, email) VALUES (?, ?, ?)", (name, time, email))
    conn.commit()
    conn.close()
    return "<p>✅ Reminder added successfully! <a href='/'>Go back</a></p>"

@app.route('/delete/<int:id>', methods=['GET'])
def delete(id):
    conn = sqlite3.connect('medicine.db')
    c = conn.cursor()
    c.execute("DELETE FROM reminders WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return "<p>🗑️ Reminder deleted! <a href='/'>Go back</a></p>"

@app.route('/clear_all', methods=['POST'])
def clear_all():
    conn = sqlite3.connect('medicine.db')
    c = conn.cursor()
    c.execute("DELETE FROM reminders")
    conn.commit()
    conn.close()
    return "<p>🧹 All reminders cleared! <a href='/'>Go back</a></p>"

# ---------------- Email Sending Function ----------------
def send_email(to_email, subject, body):
    msg = EmailMessage()
    msg["From"] = os.getenv("FROM_NAME", "Medicine Reminder")
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(os.getenv("EMAIL_HOST"), int(os.getenv("EMAIL_PORT"))) as server:
            server.starttls()
            server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
            server.send_message(msg)
            print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print("❌ Failed to send email:", e)

# ---------------- Reminder Checker ----------------
def check_reminders():
    now = datetime.now().strftime("%H:%M")
    conn = sqlite3.connect('medicine.db')
    c = conn.cursor()
    c.execute("SELECT id, name, time, email, sent FROM reminders")
    rows = c.fetchall()

    for rid, name, time_str, email, sent in rows:
        if sent == 0 and time_str == now:
            send_email(
                email,
                f"Time to take your medicine: {name}",
                f"💊 Reminder:\nIt's {time_str}, time to take your medicine: {name}."
            )
            c.execute("UPDATE reminders SET sent=1 WHERE id=?", (rid,))
            conn.commit()
    conn.close()

# ---------------- Scheduler Setup ----------------
scheduler = BackgroundScheduler()
scheduler.add_job(check_reminders, 'interval', minutes=1)
scheduler.start()

# Ensure scheduler stops cleanly
atexit.register(lambda: scheduler.shutdown(wait=False))

# ---------------- Run Server ----------------
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


