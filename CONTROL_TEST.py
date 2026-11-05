import os
import sys
import datetime

print("=== CONTROL TEST ===")
print("Workspace:", os.getcwd())
print("Python:", sys.version.split()[0])
print("Key loaded:", "YES" if os.environ.get("GNANI_API_KEY") else "NO")
print("Files here:", sorted(os.listdir(r"C:\Users\kkyea\gnani-voice-app")))
print("Time:", datetime.datetime.now().strftime("%H:%M:%S"))
print("STATUS: OPENSCHEDULE HAS CONTROL OF THIS WORKSPACE")