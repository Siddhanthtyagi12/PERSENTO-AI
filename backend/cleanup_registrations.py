import os
import sys
import pickle
import numpy as np

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import register_face
from database import db_operations

def run_cleanup():
    print("\n--- Biometric Database Cleanup ---")
    
    # 1. Load Data
    names = register_face.load_names_to_dict()
    encodings = register_face.load_encodings()
    
    if not names:
        print("[ERROR] No names found in names.txt")
        return

    # Mappings for merging: {target_id: [source_ids]}
    # Target 18 = Siddhant Tyagi
    # Source 9, 10, 11 = manager, siddhanth
    # Target 16 = Anjali kamat
    # Source 14, 17 = anjali
    merge_map = {
        18: [9, 10, 11],
        16: [14, 17]
    }
    
    all_source_ids = [s for sublist in merge_map.values() for s in sublist]
    
    for target_id, source_ids in merge_map.items():
        print(f"[INFO] Merging Source IDs {source_ids} into Target ID {target_id}...")
    
        # 2. Merge in Database
        try:
            success = db_operations.merge_users_db(target_id, source_ids)
            if not success:
                print(f"[ERROR] Database merge failed for {target_id}. Skipping local cleanup for this group.")
                continue
        except Exception as e:
            print(f"[ERROR] DB Exception: {e}")
            continue

        # 3. Clean up local encodings.pkl
        for s_id in source_ids:
            if s_id in encodings:
                del encodings[s_id]
                print(f"[LOCAL] Deleted encoding for ID {s_id}")
            
    # Save encodings
    register_face.save_encodings(encodings)
    
    # 4. Clean up names.txt
    current_names = {}
    if os.path.exists(register_face.names_file):
        with open(register_face.names_file, 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    try:
                        uid = int(parts[0])
                        if uid not in all_source_ids:
                            current_names[uid] = parts[1]
                    except: continue
    
    with open(register_face.names_file, 'w') as f:
        for uid, name in current_names.items():
            f.write(f"{uid},{name}\n")
    
    print(f"[LOCAL] Cleaned names.txt. Primary IDs remain.")
    print("--- Cleanup Complete! ---")

if __name__ == "__main__":
    run_cleanup()
