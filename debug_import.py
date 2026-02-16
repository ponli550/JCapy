import sys
import jcapy
import jcapy.commands.frameworks
import inspect

print(f"Python executable: {sys.executable}")
print(f"jcapy location: {jcapy.__file__}")
print(f"frameworks location: {jcapy.commands.frameworks.__file__}")
from jcapy.commands.frameworks import harvest_framework
print(f"harvest_framework spec: {inspect.signature(harvest_framework)}")
