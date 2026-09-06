"""Opt-in assertion over ACTUAL canonical GPU regression output, never fixtures."""

import json
import os
from pathlib import Path
import unittest


class ModelRegression(unittest.TestCase):
    @unittest.skipUnless(
        os.environ.get("STAGE_B_REGRESSION_RESULT"),
        "GPU model regression not run; set STAGE_B_REGRESSION_RESULT to its output",
    )
    def test_real_model_regression(self):
        data = json.loads(
            Path(os.environ["STAGE_B_REGRESSION_RESULT"]).read_text(encoding="utf-8")
        )
        self.assertEqual(data["signature"]["model"], "Qwen/Qwen3-8B-AWQ")
        self.assertEqual(data["signature"]["mode"], "calibration_regression_debug")
        self.assertTrue(data["complete"])
        self.assertEqual(len(data["rows"]), 12)
        for r in data["rows"]:
            with self.subTest(case=r["case_id"]):
                self.assertEqual(r["status"], "ok")
                self.assertEqual(r["prediction"], r["gold_label"])
