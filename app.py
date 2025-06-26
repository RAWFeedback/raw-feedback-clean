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

# ------------------------
# Styled Login Template
# ------------------------
STYLED_LOGIN_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Login | RAW Feedback</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/milligram/1.4.1/milligram.min.css">
  <style>
    body { padding: 2rem; background: #f4f4f4; font-family: Arial, sans-serif; }
    .container { max-width: 500px; margin: auto; background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
    h2 { text-align: center; }
    p.tagline { text-align: center; color: #888; margin-bottom: 2rem; }
    .error { color: red; text-align: center; }
  </style>
</head>
<body>
  <div class="container">
    <h2>RAW Feedback</h2>
    <p class="tagline">Real. Actionable. Worthwhile.</p>
    <form method="post">
      <label for="email">Email:</label>
      <input type="email" name="email" id="email" required>

      <label for="password">Password:</label>
      <input type="password" name="password" id="password" required>

      <input class="button-primary" type="submit" value="Login">
    </form>
    {% if error %}
      <p class="error">{{ error }}</p>
    {% endif %}
  </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = users.get(email)
        if user and user['password'] == password:
            session['email'] = email
            return redirect(url_for('feedback_form'))
        return render_template_string(STYLED_LOGIN_TEMPLATE, error="Invalid credentials.")
    return render_template_string(STYLED_LOGIN_TEMPLATE, error=None)

# ------------------------
# Styled Feedback Form
# ------------------------
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

    return render_template_string("""
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1.0'>
        <title>RAW Feedback Form</title>
        <link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/milligram/1.4.1/milligram.min.css'>
        <style>
            body { padding: 2rem; background: #f4f4f4; font-family: Arial, sans-serif; }
            .container { max-width: 700px; margin: auto; background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
            h2 { text-align: center; }
        </style>
    </head>
    <body>
        <div class='container'>
            <h2>Submit Feedback</h2>
            <p style='text-align:center; color: #888;'>for {{ email }}</p>
            <form method='post'>
                <label for='role'>Role Applied For</label>
                <input type='text' name='role' id='role' required>

                <label for='candidate_name'>Candidate Name</label>
                <input type='text' name='candidate_name' id='candidate_name' required>

                <label for='status'>Status (Yes/No)</label>
                <input type='text' name='status' id='status' required>

                <label for='positives'>Strengths</label>
                <textarea name='positives' id='positives' required></textarea>

                <label for='areas_to_improve'>Areas to Improve</label>
                <textarea name='areas_to_improve' id='areas_to_improve' required></textarea>

                <label for='additional_comments'>Additional Comments</label>
                <textarea name='additional_comments' id='additional_comments'></textarea>

                <input class='button-primary' type='submit' value='Submit Feedback'>
            </form>
        </div>
    </body>
    </html>
    """, email=email)

# ------------------------
# Thank You Page
# ------------------------
@app.route('/thank-you')
def thank_you():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Thank You!</title>
        <link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/milligram/1.4.1/milligram.min.css'>
        <style>
            body { text-align: center; padding-top: 5rem; font-family: Arial, sans-serif; background: #f4f4f4; }
            h2 { color: #333; }
            a { color: #0074d9; text-decoration: underline; }
        </style>
    </head>
    <body>
        <h2>✅ Thank you for your feedback!</h2>
        <p><a href="/feedback">Submit another</a></p>
    </body>
    </html>
    """

# ------------------------
# Save Feedback to JSON
# ------------------------
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
