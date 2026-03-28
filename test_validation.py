import cv2

def validate_camera_source(source):
    """Checks if the camera source (index or URL) is reachable."""
    try:
        src = int(source)
    except:
        src = source
        
    print(f"Testing source: {src}")
    cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(src) # Fallback
        
    if not cap.isOpened():
        return False
        
    ret, frame = cap.read()
    cap.release()
    return ret

if __name__ == "__main__":
    result = validate_camera_source(99)
    print(f"Validation result for source 99: {result}")
    
    # Also test an invalid URL
    result = validate_camera_source("http://invalid-ip:8080/video")
    print(f"Validation result for invalid URL: {result}")
