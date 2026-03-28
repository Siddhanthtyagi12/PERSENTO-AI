import cv2
import numpy as np
import os
import time
import threading
from datetime import datetime
from multiprocessing import Process, Queue, Manager
import pyttsx3
import logging

# Add root to path so we can import from 'database' folder
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import db_operations
from backend import register_face

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def log_message(msg):
    logging.info(msg)

def calculate_ear(landmarks, eye_indices):
    """Calculates Eye Aspect Ratio (EAR) for blink detection."""
    try:
        # Vertical distances
        v1 = np.linalg.norm(np.array([landmarks[eye_indices[1]].x, landmarks[eye_indices[1]].y]) - 
                            np.array([landmarks[eye_indices[5]].x, landmarks[eye_indices[5]].y]))
        v2 = np.linalg.norm(np.array([landmarks[eye_indices[2]].x, landmarks[eye_indices[2]].y]) - 
                            np.array([landmarks[eye_indices[4]].x, landmarks[eye_indices[4]].y]))
        # Horizontal distance
        h = np.linalg.norm(np.array([landmarks[eye_indices[0]].x, landmarks[eye_indices[0]].y]) - 
                           np.array([landmarks[eye_indices[3]].x, landmarks[eye_indices[3]].y]))
        return (v1 + v2) / (2.0 * h)
    except:
        return 1.0

class CameraWorker(Process):
    def __init__(self, org_id, camera_id, source, threshold, attendance_queue, shared_cache):
        super().__init__()
        self.org_id = org_id
        self.camera_id = str(camera_id)
        self.source = source
        self.threshold = threshold
        self.attendance_queue = attendance_queue
        self.shared_cache = shared_cache # Shared dict to prevent multi-camera double marking
        self.running = True

    def load_metadata(self):
        """Reloads names and encodings from disk."""
        names = register_face.load_names_to_dict()
        encods = register_face.load_encodings()
        return names, encods

    def run(self):
        log_message(f"[CAM-{self.camera_id}] Process Started. Source: {self.source}")
        
        # Initialize MediaPipe in the child process
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python.vision import FaceLandmarker, FaceLandmarkerOptions, RunningMode

        model_path = os.path.join(os.path.dirname(__file__), 'face_landmarker.task')
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=RunningMode.IMAGE,
            num_faces=1
        )
        landmarker = FaceLandmarker.create_from_options(options)

        # Initial Metadata Load
        names_dict, known_encodings_dict = self.load_metadata()
        known_ids = list(known_encodings_dict.keys())
        known_signatures = list(known_encodings_dict.values())

        # Video Setup
        try:
            src = int(self.source) if str(self.source).isdigit() else self.source
            if isinstance(src, int):
                cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)
            else:
                cap = cv2.VideoCapture(src)
        except:
            cap = cv2.VideoCapture(self.source)

        if not cap.isOpened():
            log_message(f"[ERROR-CAM-{self.camera_id}] Could not open source: {self.source}")
            return

        # Optimization Parameters
        STABILITY_FRAMES = 5
        identity_buffer = {} # {id: count}
        blink_counters = {} # {id: {'count': 0, 'blinked': False}}
        verification_feedback = {} # {id: timestamp}

        LEFT_EYE = [33, 160, 158, 133, 153, 144]
        RIGHT_EYE = [362, 385, 387, 263, 373, 380]
        EAR_THRESHOLD = 0.18
        
        last_reload_time = time.time()
        RELOAD_INTERVAL = 10 # Reload metadata every 10 seconds
        
        while self.running:
            # Periodic Metadata Reload to catch new registrations
            if time.time() - last_reload_time > RELOAD_INTERVAL:
                try:
                    new_names, new_encodings = self.load_metadata()
                    if len(new_names) != len(names_dict) or len(new_encodings) != len(known_encodings_dict):
                        log_message(f"[CAM-{self.camera_id}] New registrations detected. Reloading Metadata...")
                        names_dict, known_encodings_dict = new_names, new_encodings
                        known_ids = list(known_encodings_dict.keys())
                        known_signatures = list(known_encodings_dict.values())
                    last_reload_time = time.time()
                except Exception as e:
                    log_message(f"[ERROR-CAM-{self.camera_id}] Error reloading metadata: {e}")

            try:
                ret, frame = cap.read()
                if not ret: break
                
                display_frame = frame.copy()
                h, w, _ = frame.shape
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                
                detection_result = landmarker.detect(mp_image)
                if detection_result.face_landmarks:
                    for face_landmarks in detection_result.face_landmarks:
                        # Draw Box
                        min_x = int(min([l.x for l in face_landmarks]) * w)
                        max_x = int(max([l.x for l in face_landmarks]) * w)
                        min_y = int(min([l.y for l in face_landmarks]) * h)
                        max_y = int(max([l.y for l in face_landmarks]) * h)
                        
                        min_x, min_y = max(0, min_x), max(0, min_y)
                        max_x, max_y = min(w, max_x), min(h, max_y)
                        # Recognition Logic
                        sig = []
                        for l in face_landmarks:
                            sig.extend([l.x, l.y, l.z])
                        sig = np.array(sig)
                        sig = sig - np.mean(sig)
                        norm = np.linalg.norm(sig)
                        if norm > 0: sig = sig / norm
                        
                        user_id = None
                        user_name = "Unknown"
                        color = (0, 0, 255) # Default Red
                        display_text = "Scanning..."
                        if known_signatures:
                            distances = [np.linalg.norm(sig - ks) for ks in known_signatures]
                            best_idx = np.argmin(distances)
                            best_dist = distances[best_idx]
                            
                            # Stability Check: Only proceed if best match is significantly better than second best
                            sorted_dists = sorted(distances)
                            second_best_dist = sorted_dists[1] if len(sorted_dists) > 1 else 9.0
                            confidence_gap = second_best_dist - best_dist
                            
                            if best_dist < self.threshold and confidence_gap > 0.05:
                                user_id = known_ids[best_idx]
                                user_name = names_dict.get(user_id, "Unknown")
                                
                                # Increment buffer for this user, decay others to prevent "flickering" memory
                                identity_buffer[user_id] = min(identity_buffer.get(user_id, 0) + 1, STABILITY_FRAMES + 10)
                                for oid in list(identity_buffer.keys()):
                                    if oid != user_id:
                                        identity_buffer[oid] = max(0, identity_buffer[oid] - 1)
                                
                                if identity_buffer[user_id] >= STABILITY_FRAMES:
                                    # CHECK IF ALREADY MARKED TODAY
                                    today = datetime.now().strftime('%Y-%m-%d')
                                    cache_key = f"{user_id}_{today}"
                                    
                                    if cache_key in self.shared_cache:
                                        color = (0, 255, 0)
                                        display_text = f"{user_name}: Already Marked"
                                    else:
                                        color = (0, 165, 255) # Orange (Ready for blink)
                                        display_text = f"{user_name}: Please Blink"
                                        
                                        # Liveness: Blink Detection
                                        ear = (calculate_ear(face_landmarks, LEFT_EYE) + 
                                               calculate_ear(face_landmarks, RIGHT_EYE)) / 2.0
                                               
                                        if user_id not in blink_counters:
                                            blink_counters[user_id] = {'count': 0, 'blinked': False}
                                            
                                        if ear < EAR_THRESHOLD:
                                            blink_counters[user_id]['count'] += 1
                                        else:
                                            if blink_counters[user_id]['count'] >= 2:
                                                blink_counters[user_id]['blinked'] = True
                                            blink_counters[user_id]['count'] = 0
                                            
                                        if blink_counters[user_id]['blinked']:
                                            log_message(f"[CAM-{self.camera_id}] Queuing attendance for {user_name}")
                                            self.attendance_queue.put({
                                                'user_id': user_id, 
                                                'org_id': self.org_id,
                                                'name': user_name,
                                                'camera_id': self.camera_id
                                            })
                                            self.shared_cache[cache_key] = time.time()
                                            verification_feedback[user_id] = time.time()
                                            blink_counters[user_id]['blinked'] = False # reset
                                            
                                            color = (0, 255, 0)
                                            display_text = f"{user_name}: Verified"
                                else:
                                    color = (255, 255, 0)
                                    display_text = f"Confirming {user_name}..."
                            else:
                                color = (0, 0, 255)
                                display_text = "Unknown"
                                
                        # Draw on frame
                        if user_id in verification_feedback:
                            if time.time() - verification_feedback[user_id] < 3.0:
                                color = (0, 255, 0)
                                display_text = f"{user_name}: Verified"
                            else:
                                del verification_feedback[user_id]
                        
                        cv2.rectangle(display_frame, (min_x, min_y), (max_x, max_y), color, 2)
                        text_y = min_y - 10 if min_y - 10 > 10 else min_y + 20
                        cv2.putText(display_frame, display_text, (min_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                cv2.imshow(f"Attendance Feed - Camera {self.camera_id}", display_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            except Exception as e:
                log_message(f"[CRITICAL-ERROR-CAM-{self.camera_id}] {str(e)}")
        
        # Finally block after while loop
        if 'cap' in locals() and cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()
        log_message(f"[CAM-{self.camera_id}] Process terminated and resources released.")

class EngineOrchestrator:
    def __init__(self):
        self.manager = Manager()
        self.shared_cache = self.manager.dict()
        self.attendance_queue = Queue()
        self.active_processes = {} # {camera_id: Process}
        
        # Initialize TTS Engine
        try:
            self.engine = pyttsx3.init()
            # Set voice properties (Optional)
            self.engine.setProperty('rate', 150)
            self.engine.setProperty('volume', 1.0)
        except Exception as e:
            print(f"[ERROR] Failed to initialize TTS: {e}")
            self.engine = None

    def start_camera(self, org_id, camera_id, source, threshold):
        camera_id = str(camera_id)
        if camera_id in self.active_processes:
            self.stop_camera(camera_id)
            
        p = CameraWorker(org_id, camera_id, source, threshold, self.attendance_queue, self.shared_cache)
        p.start()
        self.active_processes[camera_id] = p

    def stop_camera(self, camera_id):
        camera_id = str(camera_id)
        if camera_id in self.active_processes:
            self.active_processes[camera_id].terminate()
            self.active_processes[camera_id].join() # Wait for process to fully terminate
            del self.active_processes[camera_id]

    def process_attendance_queue(self):
        """This should run in the main thread/process to update DB."""
        while not self.attendance_queue.empty():
            data = self.attendance_queue.get()
            try:
                # Mark in DB
                marked = db_operations.mark_attendance_db(
                    data['user_id'], 
                    data['org_id'], 
                    datetime.now().strftime('%Y-%m-%d'),
                    datetime.now().strftime('%H:%M:%S')
                )
                
                log_message(f"[ENGINE] SUCCESS: Marked Attendance for {data['name']} from Camera {data['camera_id']} (New: {marked})")
                
                # Personalized Voice Feedback
                if self.engine:
                    # Get user role for custom message
                    user_details = db_operations.get_user_details(data['user_id'])
                    role = user_details[2] if user_details else "Student"
                    
                    if role == "Teacher":
                        if marked:
                            msg = f"Aapko dekh kar acha laga Sir, Teacher {data['name']} ki attendance lag chuki hai."
                        else:
                            msg = f"Teacher {data['name']}, aapki attendance pehle hi lag chuki hai."
                    else:
                        if marked:
                            msg = f"Welcome {data['name']}, Student ki attendance lag chuki hai."
                        else:
                            msg = f"Student {data['name']}, aapki attendance pehle hi lag chuki hai."
                    
                    # Run speech in a separate thread to avoid blocking the queue processing
                    def speak_func(m):
                        try:
                            temp_engine = pyttsx3.init()
                            temp_engine.setProperty('rate', 150)
                            temp_engine.say(m)
                            temp_engine.runAndWait()
                        except: pass
                    
                    threading.Thread(target=speak_func, args=(msg,), daemon=True).start()

            except Exception as e:
                log_message(f"[ENGINE] ERROR marking attendance for {data.get('name')}: {e}")

if __name__ == "__main__":
    # Test stub
    engine = EngineOrchestrator()
