
import sys
import os
# Add current directory to path so app module can be found
sys.path.append(os.getcwd())

try:
    from app.core.config import settings
    print("Settings loaded successfully")
except Exception as e:
    print(f"Error loading settings: {e}")
    import traceback
    traceback.print_exc()
