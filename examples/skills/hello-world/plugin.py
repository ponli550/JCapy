def run_hello(args):
    print("👋 Hello from the JCapy Plugin System! (Loaded via jcapy.yaml)")

def register_commands(registry):
    registry.register("hello", run_hello, "Prints a greeting from the plugin system")
