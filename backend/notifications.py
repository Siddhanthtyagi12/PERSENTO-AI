import os
import uuid
from datetime import datetime

# A simple Mock Notification System
# This avoids any real SMS charges

LOG_FILE = os.path.join(os.path.dirname(__file__), 'sent_sms_logs.txt')

def send_absence_notification(parent_phone, student_name, class_name):
    """Mocks sending an SMS notification to parents about student absence."""
    if not parent_phone or parent_phone == 'N/A':
        return False, "Invalid phone number"

    try:
        message_body = f"Presento Alert: Your ward {student_name} ({class_name}) is ABSENT today. Please contact the school office for details."
        
        # Simulating a successful SMS sending event
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        mock_sid = f"SM{uuid.uuid4().hex[:16].upper()}"
        
        # Log to a file instead of charging money
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] SMS Sent to {parent_phone} | Message: {message_body} | SID: {mock_sid}\n")
        
        print(f"[SUCCESS] Mock SMS sent to {parent_phone} for {student_name}. Logged in {LOG_FILE}")
        return True, mock_sid
    except Exception as e:
        print(f"[ERROR] Failed to send mock notification: {e}")
        return False, str(e)

def send_whatsapp_notification(parent_phone, student_name, class_name):
    """Mocks sending a WhatsApp notification to parents about student absence."""
    if not parent_phone or parent_phone == 'N/A':
        return False, "Invalid phone number"

    try:
        message_body = f"Presento Alert: Your ward {student_name} ({class_name}) is ABSENT today. Please contact the school office for details."
        
        # Simulating a successful WhatsApp event
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        mock_sid = f"WA{uuid.uuid4().hex[:16].upper()}"
        
        # Log to the same file
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] WhatsApp Sent to {parent_phone} | Message: {message_body} | SID: {mock_sid}\n")
        
        print(f"[SUCCESS] Mock WhatsApp sent to {parent_phone} for {student_name}. Logged in {LOG_FILE}")
        return True, mock_sid
    except Exception as e:
        print(f"[ERROR] Failed to send mock WhatsApp: {e}")
        return False, str(e)
def send_fee_notification(parent_phone, student_name, due_amount):
    """Mocks sending an SMS notification to parents about pending fees."""
    if not parent_phone or parent_phone == 'N/A' or not due_amount:
        return False, "Invalid data"

    try:
        message_body = f"Presento Fee Alert: Your ward {student_name} has a pending fee balance of ₹{due_amount}. Please clear the dues to avoid any inconvenience."
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        mock_sid = f"FE{uuid.uuid4().hex[:16].upper()}"
        
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] FEE SMS Sent to {parent_phone} | Amount: ₹{due_amount} | SID: {mock_sid}\n")
        
        print(f"[SUCCESS] Fee notification sent for {student_name}. Logged in {LOG_FILE}")
        return True, mock_sid
    except Exception as e:
        print(f"[ERROR] Failed to send fee notification: {e}")
        return False, str(e)
