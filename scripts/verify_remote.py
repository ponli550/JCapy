import os
import sys
from jcapy.main import main

key = os.getenv("JCAPY_PINECONE_API_KEY", "")
print(f"DEBUG: JCAPY_PINECONE_API_KEY length: {len(key)}")
# print(f"DEBUG: JCAPY_PINECONE_API_KEY prefix: {key[:5]}") # Masked

if not key:
    print("DEBUG: Key is missing!")

os.environ["JCAPY_MEMORY_PROVIDER"] = "remote"

# Mock sys.argv
sys.argv = ["jcapy", "recall", "test query"]

if __name__ == "__main__":
    main()
