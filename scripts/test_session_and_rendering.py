"""Unit test verifying Markdown rendering sanitization, local session storage, and report recovery."""

import os
import sys
import unittest

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import sanitize_markdown_report
from crew.memory.session_manager import (
    create_session,
    save_report,
    get_report,
    get_all_sessions,
    delete_session,
    add_chat_message,
    get_chat_messages
)


class TestSessionAndRendering(unittest.TestCase):

    def test_sanitize_markdown_report(self):
        # Test stripping think tags
        raw_think = "<think>Analyzing user query and structuring output...</think>\n# Quantum Computing\nEmpirical findings."
        clean = sanitize_markdown_report(raw_think)
        self.assertNotIn("<think>", clean)
        self.assertIn("# Quantum Computing", clean)

        # Test stripping wrapping ```markdown
        raw_fenced = "```markdown\n# Header\nContent\n```"
        clean_fenced = sanitize_markdown_report(raw_fenced)
        self.assertEqual(clean_fenced, "# Header\nContent")

    def test_local_session_and_report_lifecycle(self):
        test_title = "Test Deep Research on ZKP"
        test_report = "# ZKP Architecture\n\n## Summary\nStrong proofs verified."

        # 1. Create session
        session = create_session(test_title)
        self.assertIsNotNone(session)
        s_id = session.get("id")
        self.assertTrue(len(s_id) > 10)

        # 2. Save report
        saved_rep = save_report(s_id, test_report)
        self.assertIsNotNone(saved_rep)

        # 3. Retrieve report
        retrieved_rep = get_report(s_id)
        self.assertIsNotNone(retrieved_rep)
        self.assertIn("Strong proofs verified", retrieved_rep.get("markdown_content", ""))

        # 4. Chat history
        add_chat_message(s_id, "user", "Explain verification cost")
        add_chat_message(s_id, "assistant", "Verification is O(1) in Groth16.")
        history = get_chat_messages(s_id)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[1]["content"], "Verification is O(1) in Groth16.")

        # 5. Clean up
        deleted = delete_session(s_id)
        self.assertTrue(deleted)
        self.assertIsNone(get_report(s_id))


if __name__ == "__main__":
    unittest.main()
