import os
import sys
import cv2
import numpy as np
import base64
# Add root to path so we can import from 'database' folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_cors import CORS
from database import db_operations
from datetime import datetime, timedelta
from functools import wraps

# Setup template folder path relative to this script
template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend', 'templates')
app = Flask(__name__, template_folder=template_dir)
CORS(app)
app.secret_key = 'presento_ai_secret_key_777' # Updated Brand Key
app.permanent_session_lifetime = timedelta(days=30) # Keep users logged in for 30 days

# Multi-Camera Engine Integration
from backend.camera_engine import EngineOrchestrator
import threading
import time
from backend import notifications
from database import cloud_config

# Initialize as None, will be set in main block to avoid multiprocessing loop on Windows
orchestrator = None

def background_attendance_monitor():
    """Periodically processes the queue from multiprocessing camera workers."""
    while True:
        if orchestrator:
            orchestrator.process_attendance_queue()
        time.sleep(1)

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

@app.route('/dashboard')
@login_required
def dashboard():
    # app.logger removed to prevent Errno 22
    org_id = session['org_id']
    org_name = session['org_name']
    
    # app.logger removed
    # Aaj ki date nikalna
    today = datetime.now().strftime('%Y-%m-%d')
    date_filter = request.args.get('date', today)
    
    try:
        # DB se data lana (SaaS filter)
        records = db_operations.get_all_attendance_today(org_id, date_filter)
        # app.logger removed
    except Exception as e:
        # app.logger removed
        flash("Database se haazri laane mein dikkat huyi.", "error")
        records = []
    
    student_records = []
    teacher_records = []
    class_summary = {} # {class_name: count}
    
    for row in records:
        try:
            role = row[2]
            class_name = row[3] if row[3] else "Other"
            
            if role and ('Teacher' in role or 'Sir' in role or 'Maam' in role):
                teacher_records.append(row)
            else:
                student_records.append(row)
                class_summary[class_name] = class_summary.get(class_name, 0) + 1
        except Exception as e:
            pass # Ignore row processing errors silently
            
    # app.logger removed
    
    try:
        # Short Attendance List (SaaS filter)
        short_attendance = db_operations.get_short_attendance_students(org_id, threshold=75.0)
        
        cameras = db_operations.get_org_cameras(org_id)
        # app.logger removed
        
        # app.logger removed
        return render_template('dashboard.html',
                               org_name=org_name,
                           student_records=student_records,
                           teacher_records=teacher_records,
                           class_summary=class_summary,
                           date=date_filter,
                               short_attendance=short_attendance,
                               active_page='dashboard',
                               cameras=cameras)
    except Exception as e:
        # app.logger removed
        flash("Dashboard load nahi ho paya, kripya dobara try karein.", "error")
        return redirect(url_for('login'))

@app.route('/critical')
@login_required
def critical_attendance():
    org_id = session['org_id']
    short_attendance = db_operations.get_short_attendance_students(org_id, threshold=75.0)
    return render_template('critical.html', short_attendance=short_attendance, active_page='critical')

@app.route('/registration')
@login_required
def registration_page():
    return render_template('registration.html', active_page='registration')

@app.route('/manage_users')
@login_required
def manage_users():
    org_id = session['org_id']
    users = db_operations.get_all_users(org_id)
    return render_template('manage_users.html', users=users, active_page='manage_users')

@app.route('/api/browser_register', methods=['POST'])
@login_required
def browser_register():
    data = request.json
    name = data.get('name')
    role = data.get('role')
    class_name = data.get('class_name')
    parent_phone = data.get('parent_phone')
    images = data.get('images', [])
    org_id = session['org_id']

    if not name or not images:
        return jsonify({"status": "error", "message": "Missing name or biometric data"}), 400

    try:
        from backend import register_face
        signatures = []
        
        for base64_image in images:
            header, encoded = base64_image.split(",", 1) if "," in base64_image else (None, base64_image)
            img_data = base64.b64decode(encoded)
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            sig = register_face.extract_face_signature(img)
            if sig is not None:
                signatures.append(sig)

        if not signatures:
            return jsonify({"status": "error", "message": "No face detected in any capture. Try again."}), 400

        # Mean Signature for better accuracy
        final_signature = np.mean(signatures, axis=0)
        
        # ADVANCED AI: Check for duplicates before saving
        is_dup, dup_name = register_face.check_for_duplicate_face(final_signature)
        if is_dup:
            return jsonify({
                "status": "error", 
                "message": f"Registration Blocked! Yeh face pehle se '{dup_name}' ke naam se registered hai. AI confuse nahi hoga!"
            }), 409

        # 1. Add to Supabase
        user_id = db_operations.add_user_db(name, role, class_name, parent_phone, org_id)
        
        if not user_id:
            raise Exception("Failed to generate user ID from database")

        # 2. Update Local Biometrics
        known_encodings = register_face.load_encodings()
        known_encodings[user_id] = final_signature
        register_face.names_dict[user_id] = name
        register_face.save_encodings(known_encodings)
        
        # 3. Update names.txt (Sync for monitoring)
        with open(register_face.names_file, 'a') as f:
            f.write(f"{user_id},{name}\n")
        
        return jsonify({
            "status": "success", 
            "message": f"Bachhe {name} ka registration ho gaya hai! Aapki biometrics save ho chuki hain.", 
            "name": name,
            "user_id": user_id
        }), 200


    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    org_id = session['org_id']
    from backend import register_face
    
    # 1. Clean up local files and memory maps
    register_face.cleanup_user_files(user_id)
    
    # 2. Remove from Database
    db_operations.delete_user(user_id, org_id)
    
    return f"User {user_id} deleted successfully", 200

@app.route('/manage_logs')
@login_required
def manage_logs():
    org_id = session['org_id']
    today = datetime.now().strftime('%Y-%m-%d')
    date_filter = request.args.get('date', today)
    records = db_operations.get_all_attendance_today(org_id, date_filter)
    return render_template('manage_logs.html', records=records, date=date_filter, active_page='manage_logs')

@app.route('/delete_attendance/<int:record_id>', methods=['POST'])
@login_required
def delete_attendance(record_id):
    # For extra security in SaaS, we should check if record belongs to org
    db_operations.delete_attendance_record(record_id)
    return f"Record {record_id} deleted", 200

@app.route('/live')
@login_required
def live_monitor():
    return render_template('live.html', active_page='live')

@app.route('/api/latest_logs')
@login_required
def latest_logs():
    from flask import jsonify
    org_id = session['org_id']
    today = datetime.now().strftime('%Y-%m-%d')
    records = db_operations.get_all_attendance_today(org_id, today)
    return jsonify([{
        'name': r[0],
        'time': r[1],
        'role': r[2],
        'class': r[3],
        'id': r[4]
    } for r in records])

@app.route('/register_school', methods=['GET', 'POST'])
def register_school():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        if not name or not email or not password:
            flash('All fields are required!', 'error')
            return render_template('register_school.html')
            
        try:
            org_id = db_operations.register_organization(name, email, password)
            if org_id:
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Email or School Name already registered!', 'error')
        except Exception as e:
            flash(f'Registration Error: {str(e)}', 'error')
            
    return render_template('register_school.html')

def validate_camera_source(source, org_id=None):
    """Checks if the camera source is reachable or already active."""
    source_str = str(source).strip()
    if "://" in source_str:
        return True # Trusted if it's a URL
    
    # NEW: Check if this source is already LIVE in the orchestrator to avoid 'Busy' errors
    if orchestrator and hasattr(orchestrator, 'active_processes'):
        for pid, p in orchestrator.active_processes.items():
            # Source can be int or str, normalize for comparison
            if hasattr(p, 'source') and str(p.source).strip() == source_str:
                return True # It's already in use by us, so it's valid!

    try:
        src = int(source_str)
        # Test with CAP_DSHOW first (Windows optimization)
        cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(src) # Fallback
            
        if not cap.isOpened():
            if org_id:
                cameras = db_operations.get_org_cameras(org_id)
                for cam in cameras:
                    if str(cam[1]).strip() == source_str and cam[3] == 1:
                        return True # It's already marked active in DB
            return False
            
        cap.release()
        return True
    except:
        return False

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    org_id = session['org_id']
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_camera':
            source = request.form.get('source', '').strip()
            label = request.form.get('label', '').strip()
            
            # Validation Step
            if validate_camera_source(source, org_id):
                db_operations.add_org_camera(org_id, source, label)
                flash(f'Camera "{label}" added successfully! Go to Dashboard and click "START MONITORING".', 'success')
            else:
                flash(f'Error: Camera source "{source}" is invalid or busy. Check connection.', 'error')
            
        elif action == 'delete_camera':
            cam_id = request.form.get('camera_id')
            db_operations.delete_org_camera(cam_id, org_id)
            orchestrator.stop_camera(cam_id)
            flash('Camera removed.', 'success')
            
        elif action == 'update_threshold':
            threshold = request.form.get('threshold')
            db_operations.update_org_threshold(org_id, float(threshold))
            session['recognition_threshold'] = float(threshold)
            flash('AI Precision updated!', 'success')
            
        return redirect(url_for('settings'))
        
    cameras = db_operations.get_org_cameras(org_id)
    _, threshold = db_operations.get_org_settings(org_id)
    return render_template('settings.html', cameras=cameras, current_threshold=threshold, active_page='settings')

@app.route('/toggle_camera', methods=['POST'])
@login_required
def toggle_camera():
    global orchestrator
    if orchestrator is None:
        flash('System Engine is not initialized. Please restart the dashboard.', 'error')
        return redirect(url_for('dashboard'))

    org_id = session['org_id']
    cam_id = request.form.get('camera_id')
    new_status = int(request.form.get('status'))
    
    db_operations.update_camera_status(cam_id, org_id, new_status)
    
    if new_status == 0:
        orchestrator.stop_camera(cam_id)
        flash('Camera feed stopped.', 'success')
    else:
        # Fetch camera details to start it immediately
        cameras = db_operations.get_org_cameras(org_id)
        cam_info = next((c for c in cameras if str(c[0]) == str(cam_id)), None)
        if cam_info:
            _, source, label, _ = cam_info
            _, threshold = db_operations.get_org_settings(org_id)
            orchestrator.start_camera(org_id, cam_id, source, threshold)
            flash(f'Camera {label} is now LIVE!', 'success')
        else:
            flash('Camera not found.', 'error')
            
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/start_monitoring', methods=['POST'])
@login_required
def start_monitoring():
    global orchestrator
    """Starts all active camera processes for the organization."""
    org_id = session['org_id']
    cameras = db_operations.get_org_cameras(org_id)
    _, threshold = db_operations.get_org_settings(org_id)
    
    count = 0
    for cam in cameras:
        cam_id, source, label, is_active = cam
        if is_active:
            orchestrator.start_camera(org_id, cam_id, source, threshold)
            count += 1
            
    flash(f'Successfully launched {count} camera feeds!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/stop_monitoring', methods=['POST'])
@login_required
def stop_monitoring():
    org_id = session['org_id']
    cameras = db_operations.get_org_cameras(org_id)
    for cam in cameras:
        orchestrator.stop_camera(cam[0])
    flash('All camera feeds stopped.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/reset_system', methods=['POST'])
@login_required
def reset_system():
    org_id = session['org_id']
    db_operations.reset_org_data(org_id)
    flash('System Reset Successful! All data has been cleared.', 'success')
    return redirect(url_for('settings'))

@app.route('/backup_data')
@login_required
def backup_data():
    org_id = session['org_id']
    data = db_operations.get_org_backup_data(org_id)
    import json
    from flask import Response
    
    json_data = json.dumps(data, indent=4)
    return Response(
        json_data,
        mimetype="application/json",
        headers={"Content-disposition": f"attachment; filename=Presento_Backup_{session['org_name']}.json"}
    )

@app.route('/reports')
@login_required
def reports():
    org_id = session['org_id']
    stats = db_operations.get_student_stats(org_id)
    role_dist = db_operations.get_role_distribution(org_id)
    return render_template('reports.html', stats=stats, role_dist=role_dist, active_page='reports')

@app.route('/api/stats/trends')
@login_required
def get_stats_trends():
    org_id = session['org_id']
    days = request.args.get('days', 30, type=int)
    trends = db_operations.get_attendance_trends(org_id, days)
    return {"labels": [t[0] for t in trends], "data": [t[1] for t in trends]}

@app.route('/export_report')
@login_required
def export_report():
    import pandas as pd
    from fpdf import FPDF
    import io
    from flask import send_file
    
    org_id = session['org_id']
    format = request.args.get('format', 'excel')
    stats = db_operations.get_student_stats(org_id)
    
    df = pd.DataFrame(stats)
    df.columns = ['ID', 'Name', 'Class', 'Present Days', 'Attendance %']
    
    if format == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Attendance Report')
        output.seek(0)
        return send_file(
            output, 
            as_attachment=True, 
            download_name=f"Attendance_Report_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        # PDF Generation
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(190, 10, f"Attendance Report - {session['org_name']}", ln=True, align='C')
        pdf.set_font("Arial", "", 10)
        pdf.cell(190, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
        pdf.ln(10)
        
        # Table Header
        pdf.set_font("Arial", "B", 10)
        pdf.cell(20, 10, "ID", 1)
        pdf.cell(60, 10, "Name", 1)
        pdf.cell(40, 10, "Class", 1)
        pdf.cell(30, 10, "Present", 1)
        pdf.cell(30, 10, "%", 1)
        pdf.ln()
        
        # Table Content
        pdf.set_font("Arial", "", 10)
        for s in stats:
            pdf.cell(20, 10, str(s['id']), 1)
            pdf.cell(60, 10, str(s['name']), 1)
            pdf.cell(40, 10, str(s['class']), 1)
            pdf.cell(30, 10, str(s['present_days']), 1)
            pdf.cell(30, 10, f"{s['percentage']}%", 1)
            pdf.ln()
            
        output = io.BytesIO(pdf.output())
        return send_file(
            output,
            as_attachment=True,
            download_name=f"Attendance_Report_{datetime.now().strftime('%Y-%m-%d')}.pdf",
            mimetype="application/pdf"
        )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        try:
            org = db_operations.get_organization_by_login(email, password)
            if org:
                session.permanent = True
                session['org_id'] = org[0]
                session['org_name'] = org[1]
                session['camera_index'] = org[2]
                session['recognition_threshold'] = org[3]
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid Email or Password!', 'error')
        except Exception as e:
            flash(f'Login Error: {str(e)}', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/app/login', methods=['POST'])
def mobile_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    org = db_operations.get_organization_by_login(email, password)
    if org:
        org_id, org_name, camera_index, threshold = org
        return jsonify({
            "status": "success",
            "message": "Login Successful",
            "token": f"Bearer {org_id}",
            "org_name": org_name,
            "threshold": threshold
        }), 200
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401

@app.route('/api/browser_attendance', methods=['POST'])
@login_required
def browser_attendance():
    data = request.json
    base64_image = data.get('image')
    org_id = session['org_id']
    
    if not base64_image:
        return jsonify({"status": "error", "message": "No image"}), 400
        
    try:
        header, encoded = base64_image.split(",", 1) if "," in base64_image else (None, base64_image)
        img_data = base64.b64decode(encoded)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        from backend import register_face
        signature = register_face.extract_face_signature(img)
        
        if signature is None:
            return jsonify({"status": "no_face", "message": "Face not detected"}), 200
            
        known_encodings = register_face.load_encodings()
        # Reload names from names.txt to catch new registrations
        register_face.load_names_to_dict()
        _, threshold = db_operations.get_org_settings(org_id)
        
        known_ids = list(known_encodings.keys())
        known_sigs = list(known_encodings.values())
        
        if not known_sigs:
            return jsonify({"status": "empty", "message": "No users registered"}), 200
            
        distances = [np.linalg.norm(signature - ks) for ks in known_sigs]
        best_idx = np.argmin(distances)
        
        if distances[best_idx] < threshold:
            user_id = known_ids[best_idx]
            user_name = register_face.names_dict.get(user_id) or "Unknown"
            
            # Fetch user details to get role
            user_details = db_operations.get_user_details(user_id)
            role = user_details[2] if user_details else "Student"
            
            today = datetime.now().strftime('%Y-%m-%d')
            time_now = datetime.now().strftime('%H:%M:%S')
            
            marked = db_operations.mark_attendance_db(user_id, org_id, today, time_now)
            
            if role == "Teacher":
                if marked:
                    msg = f"Aapko dekh kar acha laga Sir, Teacher {user_name} ki attendance lag chuki hai."
                else:
                    msg = f"Teacher {user_name}, aapki attendance pehle hi lag chuki hai."
            else:
                if marked:
                    msg = f"Welcome {user_name}, Student ki attendance lag chuki hai."
                else:
                    msg = f"Student {user_name}, aapki attendance pehle hi lag chuki hai."
            
            return jsonify({
                "status": "success", 
                "name": user_name, 
                "role": role,
                "message": msg
            }), 200
            
        return jsonify({"status": "unknown", "message": "Face not recognized"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Register Blueprints
from backend.smart_quiz_generator import quiz_bp
app.register_blueprint(quiz_bp)
from backend.ai_assistant import assistant_bp
app.register_blueprint(assistant_bp)

if __name__ == '__main__':
    orchestrator = EngineOrchestrator()
    monitor_thread = threading.Thread(target=background_attendance_monitor, daemon=True)
    monitor_thread.start()
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
