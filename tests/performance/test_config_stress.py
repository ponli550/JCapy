
import unittest
import time
import os
import tempfile
import shutil
# Ensure src is in path if running directly, but better to rely on PYTHONPATH
from jcapy.core.config_manager import ConfigManager

class TestConfigStress(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.test_dir, "stress_config.json")
        self.cm = ConfigManager(self.config_file)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_rapid_writes(self):
        print("\nStarting stress test: 50 sequential writes...")
        start_time = time.time()
        for i in range(50):
            # Use nested key to exercise that logic
            self.cm.set(f"stress.key_{i}", f"value_{i}")
        duration = time.time() - start_time
        print(f"Stress Test: 50 atomic writes in {duration:.4f}s")

        self.assertEqual(self.cm.get("stress.key_49"), "value_49")

        # Verify persistence
        cm2 = ConfigManager(self.config_file)
        self.assertEqual(cm2.get("stress.key_0"), "value_0")
        self.assertEqual(cm2.get("stress.key_49"), "value_49")

if __name__ == '__main__':
    unittest.main()
