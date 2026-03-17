import os
import pickle
import sys

# Add parent directory to path to import db_operations
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import db_operations

NAMES_FILE = os.path.join(os.path.dirname(__file__), 'names.txt')
ENCODINGS_FILE = os.path.join(os.path.dirname(__file__), 'encodings.pkl')

# Set of IDs we want to KEEP
KEEP_IDS = {1, 11} # 1: siddhanth tyagi, 11: kartik tyagi

def cleanup():
    print("[INFO] Starting Comprehensive Cleanup...")
    
    # 1. Cleanup names.txt
    if os.path.exists(NAMES_FILE):
        kept_names = []
        all_ids = []
        with open(NAMES_FILE, 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) == 2:
                    uid = int(parts[0])
                    all_ids.append(uid)
                    if uid in KEEP_IDS:
                        kept_names.append(line)
        
        with open(NAMES_FILE, 'w') as f:
            f.writelines(kept_names)
        print(f"[SUCCESS] Cleaned names.txt. Kept: {len(kept_names)} entries.")
    
    # 2. Cleanup encodings.pkl
    if os.path.exists(ENCODINGS_FILE):
        with open(ENCODINGS_FILE, 'rb') as f:
            encodings = pickle.load(f)
        
        new_encodings = {uid: enc for uid, enc in encodings.items() if uid in KEEP_IDS}
        
        with open(ENCODINGS_FILE, 'wb') as f:
            pickle.dump(new_encodings, f)
        print(f"[SUCCESS] Cleaned encodings.pkl. Kept: {len(new_encodings)} vectors.")

    # 3. Cleanup Database
    # We delete from DB where ID is NOT in KEEP_IDS
    # First get all IDs that should be deleted
    try:
        current_users = db_operations.get_all_users(org_id=1) 
        # get_all_users returns (id, name, role, class_name, parent_phone)
        for user in current_users:
            uid = user[0]
            if uid not in KEEP_IDS:
                print(f"[DB] Deleting user {uid}: {user[1]}")
                db_operations.delete_user(uid, org_id=1)
        print("[SUCCESS] Database sync complete.")
    except Exception as e:
        print(f"[ERROR] DB Cleanup failed: {e}")

if __name__ == "__main__":
    cleanup()
