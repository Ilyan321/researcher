"""Unit & Integration Tests for Anti-AI Humanization Engine."""

import unittest
from crew.tools.humanizer_tool import (
    clean_ai_cliches,
    calculate_burstiness,
    split_into_sentences,
    chunk_markdown,
    BANNED_AI_PATTERNS,
)
from crew.agents.humanizer import create_humanizer_agent


class TestHumanizerEngine(unittest.TestCase):

    def test_clean_ai_cliches_strips_formulaic_patterns(self):
        """Verify that all signature AI n-grams and transition clichés are purged."""
        ai_heavy_text = (
            "In this report, we delve into the multifaceted realm of artificial intelligence. "
            "It is important to note that this architecture is a testament to modern engineering, "
            "playing a pivotal role in scalability. Furthermore, moreover, in conclusion, "
            "it fosters an environment of seamless innovation underscoring the importance of safety."
        )

        cleaned = clean_ai_cliches(ai_heavy_text)

        # Assert banned words are gone
        self.assertNotIn("delve into", cleaned.lower())
        self.assertNotIn("multifaceted", cleaned.lower())
        self.assertNotIn("testament to", cleaned.lower())
        self.assertNotIn("it is important to note", cleaned.lower())
        self.assertNotIn("pivotal role", cleaned.lower())
        self.assertNotIn("furthermore", cleaned.lower())
        self.assertNotIn("moreover", cleaned.lower())
        self.assertNotIn("in conclusion", cleaned.lower())
        self.assertNotIn("underscoring the importance", cleaned.lower())
        self.assertNotIn("fosters an environment", cleaned.lower())

    def test_calculate_burstiness_metric(self):
        """Verify burstiness coefficient calculation for monotonous vs dynamic prose."""
        # Monotonous robot text (all sentences ~8 words)
        monotonous_text = (
            "The server handles incoming web traffic efficiently. "
            "The database stores all verified user records safely. "
            "The cache provides high throughput during peak load. "
            "The system monitors memory usage across all nodes."
        )
        robot_burstiness = calculate_burstiness(monotonous_text)

        # Bursty human text (mix of 3-word and 35-word sentences)
        bursty_text = (
            "Latency exploded. "
            "Under sustained benchmark saturation of forty thousand concurrent socket connections, "
            "the kernel network buffer experienced severe head-of-line blocking that completely overwhelmed the upstream proxies. "
            "The fix was trivial."
        )
        human_burstiness = calculate_burstiness(bursty_text)

        # Human burstiness must be significantly higher than robotic monotony
        self.assertGreater(human_burstiness, robot_burstiness)
        self.assertGreater(human_burstiness, 0.60)

    def test_chunk_markdown_preserves_headers(self):
        """Verify markdown section chunking respects structure."""
        doc = (
            "## Executive Summary\nKey findings go here.\n\n"
            "## Technical Architecture\nDetailed system breakdown.\n\n"
            "## Benchmark Results\nEmpirical latency numbers."
        )
        chunks = chunk_markdown(doc, max_chunk_chars=100)
        self.assertGreaterEqual(len(chunks), 2)
        self.assertTrue(all("##" in c["text"] for c in chunks))

    def test_create_humanizer_agent(self):
        """Verify the Humanizer Agent initializes with proper roles and settings."""
        agent = create_humanizer_agent()
        self.assertEqual(agent.role, "Principal Technical Editor & Anti-AI Humanization Specialist")
        self.assertTrue("Turnitin" in agent.goal or "0% AI" in agent.goal)
        self.assertFalse(agent.allow_delegation)


if __name__ == "__main__":
    unittest.main()
