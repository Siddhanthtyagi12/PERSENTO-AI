import os
import sys
from datetime import datetime

# Add root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import db_operations
from database import cloud_config

def simulate_dashboard(org_id):
    print(f"Simulating dashboard for Org ID: {org_id}")
    date_filter = datetime.now().strftime('%Y-%m-%d')
    
    try:
        # Step 1: Fetch data
        print("Fetching attendance...")
        records = db_operations.get_all_attendance_today(org_id, date_filter) or []
        print(f"Records found: {len(records)}")
        
        print("Fetching short attendance...")
        short_attendance = db_operations.get_short_attendance_students(org_id, 75.0) or []
        print(f"Short attendance count: {len(short_attendance)}")
        
        print("Fetching cameras...")
        cameras = db_operations.get_org_cameras(org_id) or []
        print(f"Cameras found: {len(cameras)}")
        
        # Step 2: Process records
        print("Processing records...")
        student_records = [r for r in records if r[2] and 'Teacher' not in r[2]]
        teacher_records = [r for r in records if r[2] and 'Teacher' in r[2]]
        print(f"Students present: {len(student_records)}")
        print(f"Staff present: {len(teacher_records)}")
        
        print("\nSIMULATION SUCCESSFUL!")
        
    except Exception as e:
        import traceback
        print("\nSIMULATION FAILED!")
        print(traceback.format_exc())

if __name__ == "__main__":
    # Test with Org ID 1 (Vidyalaya Main)
    simulate_dashboard(1)
