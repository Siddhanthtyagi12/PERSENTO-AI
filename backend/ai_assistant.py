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
        # 1. Fetch Context Data
        today = datetime.now().strftime('%Y-%m-%d')
        stats = db_operations.get_student_stats(org_id) or []
        today_attendance = db_operations.get_all_attendance_today(org_id, today) or []
        
        # 2. Build Context String
        context_data = f"Date: {today}\n\nOverall Stats:\n"
        for s in stats:
            context_data += f"- ID: {s.get('id')}, Name: {s.get('name')}, Class/Role: {s.get('class')}, Present Days: {s.get('present_days')}, Attendance: {s.get('percentage')}%\n"
            
        context_data += "\nToday's Attendance Log:\n"
        for r in today_attendance:
            context_data += f"- {r[0]} ({r[2]} - {r[3]}) marked at {r[1]}\n"

        # 3. System Prompt (Restored and Improved)
        system_prompt = f"""You are 'Vidyalaya AI', a helpful and intelligent chatbot assistant for the school principal/management.
You answer questions clearly, politely, and professionally. Use Hindi-English (Hinglish) or English as appropriate.

IMPORTANT:
1. DO NOT MAKE UP NAMES (APNE MANN SE NAAM NA BANAYEIN).
2. ONLY use the data provided in the SCHOOL DATA CONTEXT below. 
3. If the context is empty or information is missing, say: "Maaf kijiye, abhi database mein iski koi jankari nahi mili."
4. Do not provide 'sample' list unless specifically asked for an example.

--- SCHOOL DATA CONTEXT ---
{context_data if context_data.strip() else "DATABASE IS CURRENTLY EMPTY. NO DATA LOADED."}
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
