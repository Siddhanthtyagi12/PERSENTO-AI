import os
from flask import Blueprint, request, jsonify, session
from google import genai
from datetime import datetime
from database import db_operations
from functools import wraps
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))
assistant_bp = Blueprint('assistant', __name__)

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'org_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

@assistant_bp.route('/api/assistant/chat', methods=['POST'])
@login_required
def chat():
    data = request.json
    user_message = data.get('message', '').strip()
    org_id = session.get('org_id')

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    client = get_gemini_client()
    if not client:
        return jsonify({"error": "Gemini API Key missing in .env"}), 500

    try:
        # 1. Fetch Holistic Context Data
        today = datetime.now().strftime('%Y-%m-%d')
        holistic_data = db_operations.get_student_full_summary(org_id)
        today_attendance = db_operations.get_all_attendance_today(org_id, today) or []
        
        # 2. Build Context String
        context_data = f"Date: {today}\n\nSTUDENT HOLISTIC REPORTS (Attendance, Fees, Marks, Hobbies):\n"
        for s in holistic_data:
            perf_str = ", ".join(s['performance'])
            context_data += f"- {s['name']} (Class: {s['class']}): Attendance: {s['attendance']}, Fees Due: {s['fees_due']}, Progress: [{perf_str}]\n"
            
        context_data += "\nToday's Scan Logs:\n"
        for r in today_attendance:
            context_data += f"- {r[0]} ({r[2]}) appeared at {r[1]}\n"

        # 3. System Prompt (Upgraded for Holistic Reporting)
        system_prompt = f"""You are 'Vidyalaya AI', a senior school administrator's digital advisor.
You help teachers and parents understand student progress across ALL areas: Academics, Sports, Attendance, and Fees.

VOICE & TONE:
- Professional, empathetic, and encouraging.
- Use Hinglish (Hindi + English) like: "Unki performance bahut achi hai" or "Unhone Sports mein 90% score kiya hai".

REPORTING RULES:
1. When asked about a student, give a COMBINED report:
   - "Attendance kaisi hai?" -> Look at {s['attendance']}
   - "Academic results?" -> Look at {s['performance']} (Marks)
   - "Hobby/Sports?" -> Look for keywords like 'Games', 'Singing', 'Dance' in the performance list.
2. If fees are pending, mention them politely as a reminder.
3. If no record is found for a specific name, say: "Mujhe [Name] ki koi record nahi mili. Kya aapne sahi naam likha hai?"

--- SCHOOL DATA CONTEXT ---
{context_data if context_data.strip() else "DATABASE IS CURRENTLY EMPTY."}
---------------------------
"""
        
        # 4. Generate Response
        models_to_try = ['gemini-1.5-flash', 'gemini-2.5-flash', 'gemini-2.0-flash']
        reply = None
        error_msg = ""
        
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[system_prompt, f"User Question: {user_message}"]
                )
                if response and response.text:
                    reply = response.text
                    break
            except Exception as e:
                error_msg += f" {model_name} failed: {e}"
                continue
                
        if reply:
            return jsonify({"status": "success", "reply": reply})
        else:
            return jsonify({"error": f"AI Generation Failed: {error_msg}"}), 500

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Internal Error: {str(e)}"}), 500
