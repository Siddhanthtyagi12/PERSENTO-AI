import os
import sys
import pickle
import numpy as np

# Add root to path so we can import from 'database' folder
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import db_operations
from backend import register_face

def sync_all():
    print("[SYNC] Starting Biometric Alignment...")
    
    # 1. Fetch ALL users from Supabase across all orgs (global sync)
    conn = db_operations.connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM users")
    db_users = cursor.fetchall() # List of (id, name)
    conn.close()
    
    db_user_dict = {row[0]: row[1] for row in db_users}
    print(f"[SYNC] Found {len(db_user_dict)} valid users in Supabase.")
    print(f"[SYNC] Valid IDs: {list(db_user_dict.keys())}")
    
    # 2. Load Local memory
    local_encodings = register_face.load_encodings()
    print(f"[SYNC] Local Memory has {len(local_encodings)} signatures.")
    
    # 3. Filter Encodings (Only keep those that exist in DB)
    synced_encodings = {}
    cleaned_count = 0
    for uid, sig in local_encodings.items():
        if uid in db_user_dict:
            synced_encodings[uid] = sig
        else:
            cleaned_count += 1
            print(f"[SYNC] Removing Ghost ID: {uid}")
            
    # 4. Save Synced Encodings
    register_face.save_encodings(synced_encodings)
    
    # 5. Overwrite names.txt with DB data
    with open(register_face.names_file, "w") as f:
        for uid, name in db_user_dict.items():
            f.write(f"{uid},{name}\n")
            
    print(f"[SYNC] SUCCESS!")
    print(f"[SYNC] Cleaned {cleaned_count} ghost records.")
    print(f"[SYNC] Final AI memory: {len(synced_encodings)} users.")

if __name__ == "__main__":
    sync_all()
