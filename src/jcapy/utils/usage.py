
import os
import json
import sqlite3
import time
from datetime import datetime
from typing import Dict, List, Optional
from jcapy.config import JCAPY_HOME

class UsageLogManager:
    """ Manages persistent AI usage logs and session-based tracking using SQLite. """

    def __init__(self):
        self.db_path = os.path.join(JCAPY_HOME, "usage.db")
        self.legacy_log_path = os.path.join(JCAPY_HOME, "usage_log.json")
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_data = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cost": 0.0,
            "hits": 0
        }
        self._init_db()
        self._migrate_from_json()
        self.pricing_rules = self._load_pricing_rules()

    def _init_db(self):
        """ Initialize the SQLite database schema. """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    cost REAL DEFAULT 0.0
                )
            """)
            conn.commit()

    def _migrate_from_json(self):
        """ Port legacy JSON logs to SQLite if they exist. """
        if os.path.exists(self.legacy_log_path):
            try:
                with open(self.legacy_log_path, 'r') as f:
                    logs = json.load(f)

                with sqlite3.connect(self.db_path) as conn:
                    for record in logs:
                        conn.execute("""
                            INSERT INTO usage_logs (timestamp, session_id, provider, model, input_tokens, output_tokens, cost)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            record.get("timestamp"),
                            record.get("session_id", "legacy"),
                            record.get("provider", "unknown"),
                            record.get("model", "unknown"),
                            record.get("input", 0),
                            record.get("output", 0),
                            record.get("cost", 0.0)
                        ))
                    conn.commit()

                # Cleanup legacy file
                os.rename(self.legacy_log_path, self.legacy_log_path + ".bak")
            except Exception as e:
                print(f"Migration error: {e}")

    def _load_pricing_rules(self) -> Dict:
        """ Load pricing rules from config. Default to hardcoded if missing. """
        from jcapy.config import CONFIG_MANAGER
        rules = CONFIG_MANAGER.get("usage.pricing", {})
        if not rules:
            rules = {
                "gemini-1.5-flash": {"in": 0.075, "out": 0.30},
                "gpt-4o": {"in": 5.00, "out": 15.00},
                "deepseek-chat": {"in": 0.14, "out": 0.28},
                "local": {"in": 0.0, "out": 0.0}
            }
            CONFIG_MANAGER.set("usage.pricing", rules)
        return rules

    def record_hit(self, provider: str, model: str, in_tokens: int, out_tokens: int):
        """ Record a single AI interaction in the database. """
        model_key = model if model in self.pricing_rules else "local"
        rates = self.pricing_rules.get(model_key, {"in": 0, "out": 0})
        hit_cost = (in_tokens * rates["in"] + out_tokens * rates["out"]) / 1_000_000

        # Update Session Cache
        self.session_data["input_tokens"] += in_tokens
        self.session_data["output_tokens"] += out_tokens
        self.session_data["cost"] += hit_cost
        self.session_data["hits"] += 1

        # Persistent SQL Log
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO usage_logs (timestamp, session_id, provider, model, input_tokens, output_tokens, cost)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                self.session_id,
                provider,
                model,
                in_tokens,
                out_tokens,
                round(hit_cost, 6)
            ))
            conn.commit()

    def get_session_summary(self) -> Dict:
        return self.session_data

    def get_total_summary(self) -> Dict:
        """ Calculates totals across the entire SQLite history. """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT SUM(input_tokens), SUM(output_tokens), SUM(cost) FROM usage_logs")
                row = cursor.fetchone()
                return {
                    "input_tokens": int(row[0] or 0),
                    "output_tokens": int(row[1] or 0),
                    "cost": float(row[2] or 0.0)
                }
        except Exception:
            return {"input_tokens": 0, "output_tokens": 0, "cost": 0.0}

# Global singleton
USAGE_LOG_MANAGER = UsageLogManager()
