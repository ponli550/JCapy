import os
import sys
# Add src to path
sys.path.append("/Users/irfanali/Desktop/JAAVISv2.0.0/jcapy/src")
from jcapy.core.ssl_utils import generate_cert

print("Generating server certificates...")
try:
    key, cert = generate_cert("server")
    print(f"Success: {key}, {cert}")
except Exception as e:
    print(f"Error: {e}")
