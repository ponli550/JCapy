import os
import json
import unittest
import tempfile
import shutil
from jcapy.core.config_manager import ConfigManager

class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.test_dir, "config.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_config_manager_load_save(self):
        # Initialize with no file
        cm = ConfigManager(self.config_file)

        # Test default empty
        self.assertEqual(cm.get_all(), {})

        # Test set and sync get
        cm.set("theme", "dracula")
        self.assertEqual(cm.get("theme"), "dracula")

        # Test persistence
        cm2 = ConfigManager(self.config_file)
        self.assertEqual(cm2.get("theme"), "dracula")

    def test_valid_json_loading(self):
        with open(self.config_file, "w") as f:
            json.dump({"foo": "bar"}, f)

        cm = ConfigManager(self.config_file)
        self.assertEqual(cm.get("foo"), "bar")

    def test_invalid_json_handling(self):
        with open(self.config_file, "w") as f:
            f.write("{invalid-json")

        cm = ConfigManager(self.config_file)
        self.assertEqual(cm.get_all(), {})  # Should default to empty dict

    def test_nested_keys(self):
        cm = ConfigManager(self.config_file)
        cm.set("plugins.weather.city", "London")

        self.assertEqual(cm.get("plugins.weather.city"), "London")
        self.assertEqual(cm.get("plugins.weather"), {"city": "London"})
        self.assertEqual(cm.get("plugins", {}).get("weather", {}).get("city"), "London")

    def test_optimized_set(self):
        cm = ConfigManager(self.config_file)

        # Mocking App to check messages
        class MockApp:
            def __init__(self): self.msg_count = 0
            def post_message(self, msg): self.msg_count += 1

        mock_app = MockApp()
        cm.bind_app(mock_app)

        cm.set("opt.key", "value")
        self.assertEqual(mock_app.msg_count, 1)

        cm.set("opt.key", "value") # No change
        self.assertEqual(mock_app.msg_count, 1) # Should NOT increment

        cm.set("opt.key", "new_value")
        self.assertEqual(mock_app.msg_count, 2)

    def test_env_override(self):
        os.environ["JCAPY__TEST__ENV"] = "env_value"
        os.environ["JCAPY__NESTED__KEY"] = "nested_val"

        try:
            # Re-init to parse env vars
            cm = ConfigManager(self.config_file)

            # 1. Env var exists, file empty
            self.assertEqual(cm.get("test.env"), "env_value")

            # 2. Env var overrides file
            cm.set("test.env", "file_value")
            self.assertEqual(cm.get("test.env"), "env_value") # Env wins

            # 3. Nested mapping
            self.assertEqual(cm.get("nested.key"), "nested_val")

        finally:
            del os.environ["JCAPY__TEST__ENV"]
            del os.environ["JCAPY__NESTED__KEY"]


if __name__ == '__main__':
    unittest.main()
