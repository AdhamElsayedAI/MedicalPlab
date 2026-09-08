"""Unit tests for Stage-G configuration management."""

import os
import unittest
from unittest.mock import patch

from medicalplab.stage_g.config import DEFAULT_CONFIGS, load_config
from medicalplab.stage_g.models import Environment


class TestStageGConfig(unittest.TestCase):
    """Test suite for config loading and environment overrides."""

    def test_default_configs_loaded(self):
        """Verify default environments exist."""
        self.assertIn(Environment.DEVELOPMENT, DEFAULT_CONFIGS)
        self.assertIn(Environment.STAGING, DEFAULT_CONFIGS)
        self.assertIn(Environment.PRODUCTION, DEFAULT_CONFIGS)

    def test_load_config_development(self):
        """Test default development configuration."""
        cfg = load_config("development")
        self.assertEqual(cfg.env, Environment.DEVELOPMENT)
        self.assertEqual(cfg.api_version, "v1")
        self.assertEqual(cfg.rate_limit_per_minute, 60)

    def test_load_config_production(self):
        """Test production configuration."""
        cfg = load_config("production")
        self.assertEqual(cfg.env, Environment.PRODUCTION)
        self.assertEqual(cfg.rate_limit_per_minute, 300)

    def test_load_config_with_env_vars(self):
        """Verify environment variable overrides."""
        env_vars = {
            "STAGE_G_ENV": "staging",
            "STAGE_G_DB_URI": "postgresql://custom_host:5432/testdb",
            "STAGE_G_RATE_LIMIT": "250",
            "STAGE_G_LOG_LEVEL": "DEBUG",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            cfg = load_config()
            self.assertEqual(cfg.env, Environment.STAGING)
            self.assertEqual(cfg.db_uri, "postgresql://custom_host:5432/testdb")
            self.assertEqual(cfg.rate_limit_per_minute, 250)
            self.assertEqual(cfg.log_level, "DEBUG")

    def test_load_config_invalid_env_fallback(self):
        """Verify unknown env string falls back gracefully to DEVELOPMENT."""
        cfg = load_config("nonexistent_env")
        self.assertEqual(cfg.env, Environment.DEVELOPMENT)


if __name__ == "__main__":
    unittest.main()
