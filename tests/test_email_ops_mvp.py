import json
import unittest
from pathlib import Path

from email_ops_mvp import detect_prefix, detect_phishing_risk, load_routing_matrix, process_emails


class EmailOpsMVPTests(unittest.TestCase):
    def setUp(self):
        self.matrix = load_routing_matrix(Path("config/routing_matrix.csv"))
        self.emails = json.loads(Path("samples/mock_emails.json").read_text(encoding="utf-8"))

    def test_detect_prefix_gov(self):
        prefix = detect_prefix(self.emails[0])
        self.assertEqual(prefix, "GOV")

    def test_detect_phishing_high(self):
        risk = detect_phishing_risk(self.emails[4])
        self.assertIn(risk, {"high", "medium"})

    def test_process_outputs_required_fields(self):
        results = process_emails(self.emails, self.matrix)
        self.assertEqual(len(results), 5)
        self.assertTrue(all(r.owner for r in results))
        self.assertTrue(all(r.summary_action for r in results))


if __name__ == "__main__":
    unittest.main()
