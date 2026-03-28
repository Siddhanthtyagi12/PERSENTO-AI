import os
import sys
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from functools import wraps

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db_operations
from database import cloud_config
from backend.smart_quiz_generator import quiz_bp
import cv2
import numpy as np
import base64
from backend import register_face

# Templates path
template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend', 'templates')
app = Flask(__name__, template_folder=template_dir)
CORS(app)
app.secret_key = 'presento_ai_cloud_key_888'
app.permanent_session_lifetime = timedelta(days=30)

# Register Blueprints
app.register_blueprint(quiz_bp)

# Force Propagate Exceptions for detail
app.config['PROPAGATE_EXCEPTIONS'] = True

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

@app.route('/register_school', methods=['GET', 'POST'])
def register_school():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        if not name or not email or not password:
            flash('All fields are required!', 'error')
            return render_template('register_school.html', is_cloud=True)
            
        try:
            org_id = db_operations.register_organization(name, email, password)
            if org_id:
                flash('Registration Successful! Please Login', 'success')
                return redirect(url_for('login'))
            else:
                flash('Email already registered or error occurred', 'error')
        except Exception as e:
            flash(f'Registration Error: {str(e)}', 'error')
    return render_template('register_school.html', is_cloud=True)

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
            flash('Invalid Email or Password', 'error')
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
        
        student_records = [r for r in records if r[2] and 'Teacher' not in (r[2] or '')]
        teacher_records = [r for r in records if r[2] and 'Teacher' in (r[2] or '')]
        
        return render_template('dashboard.html', 
                               org_name=session.get('org_name', 'Presento'),
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
        db_hint = ""
        if "connection" in str(e).lower() or "timeout" in str(e).lower():
            db_hint = """
            <div style="margin-top:20px; padding:15px; background:#eef2ff; border-left:5px solid #4f46e5; color:#3730a3;">
                <strong>Troubleshooting Tip:</strong> Database connection fail ho raha hai. 
                <ul style="margin-top:10px;">
                    <li>Supabase me <strong>'Allow All IPs' (0.0.0.0/0)</strong> check karein.</li>
                    <li>Environment Variable <strong>DB_CONNECTION_STRING</strong> sahi se set hai?</li>
                    <li>SSL MODE <strong>'sslmode=require'</strong> URL me hona chahiye.</li>
                </ul>
            </div>
            """
        
        return f"""
        <div style="font-family: sans-serif; padding: 40px; background: #fff5f5; color: #c53030; border-radius: 12px; border: 1px solid #feb2b2; max-width: 800px; margin: 40px auto;">
            <h1 style="margin-top: 0;">Dashboard Error</h1>
            <p>Something went wrong while loading the dashboard.</p>
            {db_hint}
            <pre style="background: #fff; padding: 15px; border-radius: 8px; border: 1px solid #fed7d7; white-space: pre-wrap; margin-top:20px;">{str(e)}\n\n{error_details}</pre>
        </div>
        """, 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ==========================================
# 4. WEB DASHBOARD ROUTES (Ported from Local)
# ==========================================

@app.route('/registration')
@login_required
def registration():
    return render_template('registration.html', active_page='registration', is_cloud=True)

@app.route('/register', methods=['POST'])
@login_required
def register():
    # Registration on cloud is restricted because it requires direct camera access
    # However, we can still show a helpful error/status
    flash('Camera-based Registration is only supported on the Local Hub (Laptop). Please register students there; they will automatically sync to this cloud dashboard.', 'info')
    return redirect(url_for('registration'))

@app.route('/toggle_camera', methods=['POST'])
@login_required
def toggle_camera():
    org_id = session['org_id']
    cam_id = request.form.get('camera_id')
    new_status = int(request.form.get('status'))
    db_operations.update_camera_status(cam_id, org_id, new_status)
    flash(f"Camera status updated in database.", 'success')
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/start_monitoring', methods=['POST'])
@login_required
def start_monitoring():
    flash('Monitoring Fleet started (Status updated). Note: Active camera processing happens on your Local Hub/Laptop.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/stop_monitoring', methods=['POST'])
@login_required
def stop_monitoring():
    flash('All camera monitoring stopped.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/send_absence_notifications', methods=['POST'])
@login_required
def send_absence_notifications():
    from backend import notifications
    org_id = session['org_id']
    today = datetime.now().strftime('%Y-%m-%d')
    absent_students = db_operations.get_absent_students(org_id, today)
    
    if not absent_students:
        flash('No absent students found today.', 'info')
        return redirect(url_for('dashboard'))
        
    success_count = 0
    for student in absent_students:
        sid, name, phone, class_name = student
        if phone and phone != 'N/A':
            success, _ = notifications.send_absence_notification(phone, name, class_name)
            if success: success_count += 1
            
    flash(f'Sent {success_count} absence notifications via Twilio Cloud.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    org_id = session['org_id']
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_camera':
            source = request.form.get('source', '').strip()
            label = request.form.get('label', '').strip()
            db_operations.add_org_camera(org_id, source, label)
            flash('Camera added successfully!', 'success')
        elif action == 'delete_camera':
            cam_id = request.form.get('camera_id')
            db_operations.delete_org_camera(cam_id, org_id)
            flash('Camera removed.', 'success')
        elif action == 'update_threshold':
            threshold = request.form.get('threshold')
            db_operations.update_org_threshold(org_id, float(threshold))
            flash('AI Precision updated!', 'success')
            
        return redirect(url_for('settings'))

    cameras = db_operations.get_org_cameras(org_id)
    _, threshold = db_operations.get_org_settings(org_id)
    return render_template('settings.html', cameras=cameras, current_threshold=threshold, active_page='settings', is_cloud=True)

@app.route('/live')
@login_required
def live_monitor():
    return render_template('live.html', active_page='live', is_cloud=True)

@app.route('/api/latest_logs')
@login_required
def latest_logs():
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

@app.route('/reports')
@login_required
def reports():
    org_id = session['org_id']
    stats = db_operations.get_student_stats(org_id)
    role_dist = db_operations.get_role_distribution(org_id)
    return render_template('reports.html', stats=stats, role_dist=role_dist, active_page='reports', is_cloud=True)

@app.route('/critical')
@login_required
def critical_attendance():
    org_id = session['org_id']
    short_attendance = db_operations.get_short_attendance_students(org_id, threshold=75.0)
    return render_template('critical.html', short_attendance=short_attendance, active_page='critical', is_cloud=True)

@app.route('/api/stats/trends')
@login_required
def get_stats_trends():
    org_id = session['org_id']
    days = request.args.get('days', 30, type=int)
    trends = db_operations.get_attendance_trends(org_id, days)
    return {"labels": [t[0] for t in trends], "data": [t[1] for t in trends]}

@app.route('/manage_users')
@login_required
def manage_users():
    org_id = session['org_id']
    users = db_operations.get_all_users(org_id)
    return render_template('manage_users.html', users=users, active_page='manage_users', is_cloud=True)

@app.route('/manage_logs')
@login_required
def manage_logs():
    org_id = session['org_id']
    today = datetime.now().strftime('%Y-%m-%d')
    date_filter = request.args.get('date', today)
    records = db_operations.get_all_attendance_today(org_id, date_filter)
    return render_template('manage_logs.html', records=records, date=date_filter, active_page='manage_logs', is_cloud=True)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    org_id = session['org_id']
    try:
        db_operations.delete_user(user_id, org_id)
        return f"User {user_id} deleted successfully", 200
    except Exception as e:
        return str(e), 500

@app.route('/delete_attendance/<int:record_id>', methods=['POST'])
@login_required
def delete_attendance(record_id):
    try:
        db_operations.delete_attendance_record(record_id)
        return f"Record {record_id} deleted", 200
    except Exception as e:
        return str(e), 500

@app.route('/reset_system', methods=['POST'])
@login_required
def reset_system():
    org_id = session['org_id']
    try:
        db_operations.reset_org_data(org_id)
        flash('System Reset Successful!', 'success')
    except Exception as e:
        flash(f'Reset Failed: {str(e)}', 'error')
    return redirect(url_for('settings'))

@app.route('/backup_data')
@login_required
def backup_data():
    org_id = session['org_id']
    try:
        data = db_operations.get_org_backup_data(org_id)
        import json
        from flask import Response
        json_data = json.dumps(data, indent=4)
        app.secret_key = 'presento_ai_cloud_key_888'
        return Response(
            json_data,
            mimetype="application/json",
            headers={"Content-disposition": f"attachment; filename=Presento_Backup.json"}
        )
    except Exception as e:
        return str(e), 500

@app.route('/export_report')
@login_required
def export_report():
    import pandas as pd
    import io
    from flask import send_file
    from datetime import datetime
    
    org_id = session['org_id']
    format_type = request.args.get('format', 'excel')
    try:
        stats = db_operations.get_student_stats(org_id)
        df = pd.DataFrame(stats)
        
        output = io.BytesIO()
        if format_type == 'excel':
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            output.seek(0)
            return send_file(output, as_attachment=True, download_name=f"Report_{datetime.now().strftime('%Y%m%d')}.xlsx")
        else:
            # Simple CSV fallback for PDF if fpdf not in cloud requirements yet
            df.to_csv(output, index=False)
            output.seek(0)
            return send_file(output, as_attachment=True, download_name=f"Report_{datetime.now().strftime('%Y%m%d')}.csv")
    except Exception as e:
        return str(e), 500

@app.route('/send_absence_notifications', methods=['POST'])
@login_required
def send_absence_notifications():
    from backend import notifications
    org_id = session['org_id']
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 1. Get absent students
    absent_students = db_operations.get_absent_students(org_id, today)
    
    if not absent_students:
        flash('All students are present! No notifications needed.', 'info')
        return redirect(url_for('dashboard'))
        
    # 2. Trigger notifications
    success_count = 0
    fail_count = 0
    
    for student in absent_students:
        sid, name, phone, class_name = student
        # Skip if no phone number
        if not phone or phone == 'N/A':
            fail_count += 1
            continue
            
        success, _ = notifications.send_absence_notification(phone, name, class_name)
        if success:
            success_count += 1
        else:
            fail_count += 1
            
    flash(f'Absence Alerts: {success_count} sent successfully. {fail_count} failed/skipped.', 'success' if success_count > 0 else 'error')
    return redirect(url_for('dashboard'))

# Hardware Placeholder Routes (To prevent 404)
@app.route('/toggle_camera', methods=['POST'])
@app.route('/start_monitoring', methods=['POST'])
@app.route('/stop_monitoring', methods=['POST'])
def hardware_stub():
    flash('Hardware controls (Webcam/RTSP) require the Local Desktop Hub.', 'info')
    return redirect(url_for('dashboard'))

# ==========================================
# 5. MOBILE APP API ROUTES (Integrated)
# ==========================================
def require_api_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401
        try:
            org_id = int(token.split(" ")[1])
            request.org_id = org_id
        except (ValueError, IndexError):
            return jsonify({"error": "Invalid Token"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/app/login', methods=['POST'])
def mobile_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    try:
        org = db_operations.get_organization_by_login(email, password)
        if org:
            org_id, org_name, _, threshold = org
            return jsonify({
                "status": "success",
                "message": "Login Successful",
                "token": f"Bearer {org_id}",
                "org_name": org_name,
                "threshold": threshold
            }), 200
    except:
        pass
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401

@app.route('/api/app/dashboard', methods=['GET'])
@require_api_token
def mobile_dashboard():
    org_id = request.org_id
    today = datetime.now().strftime('%Y-%m-%d')
    try:
        today_records = db_operations.get_all_attendance_today(org_id, today) or []
        stats = db_operations.get_student_stats(org_id) or []
        short_attendance = db_operations.get_short_attendance_students(org_id, 75.0) or []
        
        return jsonify({
            "status": "success",
            "date": today,
            "total_present_today": len(today_records),
            "total_students": len(stats),
            "critical_attendance_count": len(short_attendance),
            "recent_logs": [{"name": r[0], "time": r[1], "role": r[2], "class": r[3]} for r in today_records[:10]]
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/app/mark_attendance', methods=['POST'])
@require_api_token
def mobile_mark_attendance():
    data = request.json
    base64_image = data.get('image')
    org_id = request.org_id
    if not base64_image:
        return jsonify({"status": "error", "message": "No image provided"}), 400
    try:
        img_data = base64.b64decode(base64_image.split(',')[1] if ',' in base64_image else base64_image)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        signature = register_face.extract_face_signature(img)
        if signature is None:
            return jsonify({"status": "error", "message": "Face not detected properly."}), 400
            
        known_encodings = register_face.load_encodings()
        _, threshold = db_operations.get_org_settings(org_id)
        
        known_ids = list(known_encodings.keys())
        known_sigs = list(known_encodings.values())
        
        if not known_sigs:
            return jsonify({"status": "error", "message": "Database is empty."}), 404
            
        distances = [np.linalg.norm(signature - ks) for ks in known_sigs]
        best_idx = np.argmin(distances)
        if distances[best_idx] < threshold:
            user_id = known_ids[best_idx]
            today = datetime.now().strftime('%Y-%m-%d')
            time_now = datetime.now().strftime('%H:%M:%S')
            user_name = register_face.names_dict.get(user_id) or "Unknown"
            db_operations.mark_attendance_db(user_id, org_id, today, time_now)
            return jsonify({"status": "success", "message": f"Attendance marked for {user_name}!"}), 200
        return jsonify({"status": "error", "message": "Face not recognized."}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/browser_attendance', methods=['POST'])
@login_required
def browser_attendance():
    data = request.json
    base64_image = data.get('image')
    org_id = session['org_id']
    
    if not base64_image:
        return jsonify({"status": "error", "message": "No image"}), 400
        
    try:
        # Decode image
        header, encoded = base64_image.split(",", 1) if "," in base64_image else (None, base64_image)
        img_data = base64.b64decode(encoded)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Recognize
        from backend import register_face
        signature = register_face.extract_face_signature(img)
        
        if signature is None:
            return jsonify({"status": "no_face", "message": "Face not detected"}), 200
            
        known_encodings = register_face.load_encodings()
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
            
            today = datetime.now().strftime('%Y-%m-%d')
            time_now = datetime.now().strftime('%H:%M:%S')
            
            marked = db_operations.mark_attendance_db(user_id, org_id, today, time_now)
            return jsonify({
                "status": "success", 
                "name": user_name, 
                "message": f"Welcome, {user_name}!"
            }), 200
            
        return jsonify({"status": "unknown", "message": "Face not recognized"}), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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
        
        return jsonify({"status": "success", "message": f"Successfully enrolled {name}", "user_id": user_id}), 200


    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/manage_users')
@login_required
def manage_users():
    org_id = session['org_id']
    users = db_operations.get_all_users(org_id)
    return render_template('manage_users.html', users=users, active_page='manage_users')

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    org_id = session['org_id']
    db_operations.delete_user(user_id, org_id)
    # Also clean up local files if they exist (for hybrid cloud/local setups)
    try:
        register_face.cleanup_user_files(user_id)
    except:
        pass
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
    db_operations.delete_attendance_record(record_id)
    return f"Record {record_id} deleted", 200

@app.route('/reports')
@login_required
def reports():
    org_id = session['org_id']
    stats = db_operations.get_student_stats(org_id)
    role_dist = db_operations.get_role_distribution(org_id)
    return render_template('reports.html', stats=stats, role_dist=role_dist, active_page='reports')

@app.route('/export_report')
@login_required
def export_report():
    import pandas as pd
    from fpdf import FPDF
    import io
    from flask import send_file
    
    org_id = session['org_id']
    fmt = request.args.get('format', 'excel')
    stats = db_operations.get_student_stats(org_id)
    
    df = pd.DataFrame(stats)
    df.columns = ['ID', 'Name', 'Class', 'Present Days', 'Attendance %']
    
    if fmt == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Attendance Report')
        output.seek(0)
        return send_file(output, as_attachment=True, download_name=f"Report_{datetime.now().strftime('%Y%m%d')}.xlsx")
    else:
        pdf = FPDF()
        pdf.add_page(); pdf.set_font("Arial", "B", 16)
        pdf.cell(190, 10, f"Attendance Report - {session['org_name']}", ln=True, align='C')
        pdf.set_font("Arial", "", 10)
        for s in stats:
            pdf.cell(190, 8, f"{s['id']} | {s['name']} | {s['class']} | {s['percentage']}%", ln=True)
        output = io.BytesIO(pdf.output())
        return send_file(output, as_attachment=True, download_name=f"Report_{datetime.now().strftime('%Y%m%d')}.pdf")

@app.route('/backup_data')
@login_required
def backup_data():
    org_id = session['org_id']
    data = db_operations.get_org_backup_data(org_id)
    return jsonify(data)

@app.route('/reset_system', methods=['POST'])
@login_required
def reset_system():
    org_id = session['org_id']
    db_operations.reset_org_data(org_id)
    flash('System Reset Successful!', 'success')
    return redirect(url_for('settings'))

# Register Smart Quiz
app.register_blueprint(quiz_bp)

# Register AI Chatbot Assistant
from backend.ai_assistant import assistant_bp
app.register_blueprint(assistant_bp)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
