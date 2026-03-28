import os
from google import genai
try:
    client = genai.Client(api_key='AIzaSyC5Ycol4twbB-uxYivkFCzxgWPC9t2pr10')
    response = client.models.generate_content(model='gemini-1.5-flash', contents='hello')
    print("SUCCESS 1.5:", response.text)
except Exception as e:
    import traceback
    traceback.print_exc()

try:
    client = genai.Client(api_key='AIzaSyC5Ycol4twbB-uxYivkFCzxgWPC9t2pr10')
    response = client.models.generate_content(model='gemini-1.5-flash-8b', contents='hello')
    print("SUCCESS 1.5-8b:", response.text)
except Exception as e:
    import traceback
    traceback.print_exc()
