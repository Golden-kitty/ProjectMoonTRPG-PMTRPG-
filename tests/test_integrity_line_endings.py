import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_table_integrity import digest, git_text_digest


class IntegrityLineEndingTests(unittest.TestCase):
    def test_git_review_ignores_checkout_crlf_but_not_content(self):
        self.assertEqual(git_text_digest(b"a\r\nb\r\n"), git_text_digest(b"a\nb\n"))
        self.assertNotEqual(git_text_digest(b"a\r\nb\r\n"), git_text_digest(b"a\nc\n"))
        self.assertIsNone(git_text_digest(None))

    def test_frozen_raw_hash_remains_byte_exact(self):
        self.assertNotEqual(digest(b"a\r\n"), digest(b"a\n"))


if __name__ == "__main__":
    unittest.main()
