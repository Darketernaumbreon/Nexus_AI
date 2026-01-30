
import sys
import os
from jose import jwt
from datetime import datetime, timedelta

# Setup path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def test_jwt():
    print("Testing JWT Signing...")
    try:
        # Debug: Print key details (first line)
        key_type = type(settings.PRIVATE_KEY)
        print(f"Key Type: {key_type}")
        if isinstance(settings.PRIVATE_KEY, bytes):
            print(f"Key Length: {len(settings.PRIVATE_KEY)}")
            print(f"Key First 20 bytes: {settings.PRIVATE_KEY[:20]}")
        
        to_encode = {"sub": "test_user", "exp": datetime.utcnow() + timedelta(minutes=30)}
        
        # Attempt Encode
        print(f"Algorithm: {settings.ALGORITHM}")
        encoded_jwt = jwt.encode(to_encode, settings.PRIVATE_KEY, algorithm=settings.ALGORITHM)
        print(f"✅ JWT Generated successfully: {encoded_jwt[:20]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_jwt()
