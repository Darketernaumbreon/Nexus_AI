
import time
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["argon2"], 
    deprecated="auto",
    argon2__rounds=1, 
    argon2__memory_cost=65536,
    argon2__parallelism=4
)

start = time.time()
h = pwd_context.hash("testpassword")
end = time.time()
print(f"Hash time: {end - start:.4f}s")

start = time.time()
pwd_context.verify("testpassword", h)
end = time.time()
print(f"Verify time: {end - start:.4f}s")
