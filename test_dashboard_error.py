import sys
import os

# Create a test setup
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))
sys.path.append(os.path.join(os.path.dirname(__file__), "database"))

from backend.app import app
import json

app.config['TESTING'] = True

with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['org_id'] = 1
        sess['org_name'] = "Test Org"
        sess['camera_index'] = 0
        sess['recognition_threshold'] = 0.45

    try:
        response = client.get('/dashboard')
        print(f"Status Code: {response.status_code}")
    except Exception as e:
        import traceback
        traceback.print_exc()
