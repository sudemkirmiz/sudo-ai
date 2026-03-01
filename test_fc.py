import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def dummy_api_call():
    """This function is just a dummy tool."""
    return True

model = genai.GenerativeModel("models/gemini-2.5-flash", tools=[dummy_api_call])
chat = model.start_chat()
response = chat.send_message("Please call the dummy_api_call function.")

print(dir(response))
if hasattr(response, 'function_call'):
    print("HAS function_call:", getattr(response, 'function_call', None))
if hasattr(response, 'parts'):
    for p in response.parts:
        print("Part attributes:", dir(p))
        if hasattr(p, 'function_call'):
            print("p.function_call:", p.function_call)
