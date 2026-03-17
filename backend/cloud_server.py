import os
import sys
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_cors import CORS
from datetime import datetime
from functools import wraps

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db_operations
from database import cloud_config

# Templates path
template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend', 'templates')
app = Flask(__name__, template_folder=template_dir)
CORS(app)
app.secret_key = 'vidyalaya_ai_cloud_key_999'

# Load settings from environment variables if they exist (for Render)
USE_CLOUD = os.environ.get('USE_CLOUD', str(cloud_config.USE_CLOUD)).lower() == 'true'
DB_URL = os.environ.get('DB_CONNECTION_STRING', cloud_config.DB_CONNECTION_STRING)

# Update cloud_config dynamically and FORCE SSL if missing
if DB_URL and "sslmode=require" not in DB_URL:
    if "?" in DB_URL:
        DB_URL += "&sslmode=require"
    else:
        DB_URL += "?sslmode=require"

cloud_config.USE_CLOUD = USE_CLOUD
cloud_config.DB_CONNECTION_STRING = DB_URL

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'org_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index_page():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('username')
        password = request.form.get('password')
        try:
            org = db_operations.get_organization_by_login(email, password)
            if org:
                session['org_id'] = org[0]
                session['org_name'] = org[1]
                return redirect(url_for('dashboard'))
            flash('Invalid Credentials', 'error')
        except Exception as e:
            flash(f'Database Error: {str(e)}', 'error')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    org_id = session['org_id']
    today = datetime.now().strftime('%Y-%m-%d')
    date_filter = request.args.get('date', today)
    
    try:
        # Fetch data from DB
        records = db_operations.get_all_attendance_today(org_id, date_filter) or []
        short_attendance = db_operations.get_short_attendance_students(org_id, 75.0) or []
        cameras = db_operations.get_org_cameras(org_id) or []
        
        student_records = [r for r in records if r[2] and 'Teacher' not in r[2]]
        teacher_records = [r for r in records if r[2] and 'Teacher' in r[2]]
        
        return render_template('dashboard.html', 
                               org_name=session['org_name'],
                               student_records=student_records, 
                               teacher_records=teacher_records, 
                               short_attendance=short_attendance,
                               cameras=cameras,
                               date=date_filter,
                               active_page='dashboard',
                               is_cloud=True)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        # Log to stdout for Render logs
        print(f"DASHBOARD ERROR:\n{error_details}")
        
        # Friendly error message for the user with details for us to debug
        return f"""
        <div style="font-family: sans-serif; padding: 40px; background: #fff5f5; color: #c53030; border-radius: 12px; border: 1px solid #feb2b2; max-width: 800px; margin: 40px auto;">
            <h1 style="margin-top: 0;">Oops! Something went wrong on the Cloud.</h1>
            <p>Aapka Dashboard connect nahi ho pa raha hai. Ye details hamare liye zaroori hain:</p>
            <div style="background: #fff; padding: 15px; border-radius: 8px; border: 1px solid #fed7d7; font-family: monospace; white-space: pre-wrap; font-size: 13px; color: #2d3748;">
{str(e)}<br><br>
<b>Database URL:</b> {cloud_config.DB_CONNECTION_STRING.split('@')[-1] if cloud_config.DB_CONNECTION_STRING else 'Missing'}
            </div>
            <p style="margin-bottom: 0; margin-top: 20px;"><b>Kya karein?</b> Iska ek screenshot muje bhej dijiye taaki main turant theek kar sakun.</p>
        </div>
        """, 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# API for Mobile App
@app.route('/api/app/login', methods=['POST'])
def mobile_login():
    data = request.json
    org = db_operations.get_organization_by_login(data.get('email'), data.get('password'))
    if org:
        return jsonify({"status": "success", "token": f"Bearer {org[0]}", "org_name": org[1]}), 200
    return jsonify({"status": "error"}), 401

if __name__ == '__main__':
    # Cloud doesn't need the camera orchestrator
    app.run(host='0.0.0.0', port=8000)
