!pip install flask, gunicorn 
from flask import Flask, render_template_string, request, redirect, url_for, session
import json
import datetime
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'

USERS_FILE = 'users.json'
FEEDBACK_FILE = 'raw_feedback_web.json'

if os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
else:
    users = {
        'alice@example.com': {'password': 'password123', 'tier': 'Starter', 'used_this_month': 0},
        'bob@example.com': {'password': 'securepass', 'tier': 'Professional', 'used_this_month': 0},
        'admin@example.com': {'password': 'adminpass', 'tier': 'Enterprise', 'used_this_month': 0}
    }
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

limits = {'Starter': 10, 'Professional': 100, 'Enterprise': float('inf')}

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = users.get(email)
        if user and user['password'] == password:
            session['email'] = email
            return redirect(url_for('feedback_form'))
        return "Invalid credentials."
    return '''<form method="post"><input name="email"><input name="password" type="password"><input type="submit"></form>'''

@app.route('/feedback', methods=['GET', 'POST'])
def feedback_form():
    email = session.get('email')
    if not email:
        return redirect(url_for('login'))

    user = users[email]
    used = user['used_this_month']
    limit = limits[user['tier']]

    if request.method == 'POST':
        if used >= limit:
            return "Feedback limit reached."
        feedback = {
            "timestamp": datetime.datetime.now().isoformat(),
            "user": email,
            "role": request.form['role'],
            "candidate_name": request.form['candidate_name'],
            "status": request.form['status'],
            "positives": request.form['positives'],
            "areas_to_improve": request.form['areas_to_improve'],
            "additional_comments": request.form.get('additional_comments', '')
        }
        save_feedback(feedback)
        users[email]['used_this_month'] += 1
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=4)
        return redirect(url_for('thank_you'))

    return f"<h1>Feedback Form for {email}</h1><form method='post'><input name='role'><input name='candidate_name'><input name='status'><textarea name='positives'></textarea><textarea name='areas_to_improve'></textarea><textarea name='additional_comments'></textarea><input type='submit'></form>"

@app.route('/thank-you')
def thank_you():
    return "Thank you for your feedback."

def save_feedback(feedback, filename=FEEDBACK_FILE):
    try:
        with open(filename, "r") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    data.append(feedback)
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)

if __name__ == '__main__':
    app.run(debug=True)
