import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_FILES = (
    ROOT / "skills" / "codex-review" / "SKILL.md",
    ROOT / "skills" / "grill-me-codex" / "SKILL.md",
    ROOT / "skills" / "grill-with-docs-codex" / "SKILL.md",
)


class MonitoringGuidanceTests(unittest.TestCase):
    def test_each_skill_documents_status_and_preflight(self):
        required_text = (
            "CODEX_CLI: CHECKING",
            "CODEX_CLI: BLOCKED",
            "CODEX_REVIEW: RUNNING",
            "BLOCKED",
            "PLAN-REVIEW-LOG.md",
            "codex --version",
            "0.130",
            "unparseable",
            "There is no separate",
        )

        for path in SKILL_FILES:
            with self.subTest(skill=path.parent.name):
                content = path.read_text(encoding="utf-8")
                for text in required_text:
                    self.assertIn(text, content)

    def test_review_commands_preserve_read_only_and_surface_errors(self):
        for path in SKILL_FILES:
            with self.subTest(skill=path.parent.name):
                content = path.read_text(encoding="utf-8")
                code_blocks = "\n".join(
                    re.findall(r"```bash\n(.*?)```", content, flags=re.DOTALL)
                )
                self.assertIn("set -o pipefail", code_blocks)
                self.assertIn("-s read-only", code_blocks)
                self.assertIn('sandbox_mode="read-only"', code_blocks)
                self.assertNotIn("2>/dev/null", code_blocks)
                self.assertNotIn(">/dev/null", code_blocks)

    def test_failed_or_malformed_reviews_are_not_verdicts(self):
        for path in SKILL_FILES:
            with self.subTest(skill=path.parent.name):
                content = path.read_text(encoding="utf-8")
                self.assertIn("VERDICT: APPROVED", content)
                self.assertIn("VERDICT: REVISE", content)
                self.assertRegex(content, r"(?i)(malformed|invalid).*BLOCKED|BLOCKED.*(malformed|invalid)")


if __name__ == "__main__":
    unittest.main()
