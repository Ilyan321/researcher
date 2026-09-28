"""Unit & integration test verifying Groq API error unwrapping, model cascades, and context recovery."""

import sys
import os
import json
import unittest
from unittest.mock import patch, MagicMock
import urllib.error

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import DEFAULT_MODEL, get_llm
from app import call_groq_api
from crew.utils.editor import execute_llm_call


class TestGroqErrorHandlingAndRecovery(unittest.TestCase):

    def test_default_model_configuration(self):
        """Test that default model is set to a valid 128k context production model."""
        self.assertIn("llama-3.3-70b-versatile", DEFAULT_MODEL)

    @patch("urllib.request.urlopen")
    def test_context_length_400_auto_recovery(self, mock_urlopen):
        """Simulate a Groq 400 context_length_exceeded error followed by successful retry."""
        # 1st attempt: 400 Bad Request with context_length_exceeded
        err_response_body = json.dumps({
            "error": {
                "message": "This model's maximum context length is 8192 tokens. However, your messages resulted in 9000 tokens.",
                "type": "invalid_request_error",
                "code": "context_length_exceeded"
            }
        }).encode("utf-8")

        mock_err = urllib.error.HTTPError(
            url="https://api.groq.com/openai/v1/chat/completions",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=None,
        )
        mock_err.read = MagicMock(return_value=err_response_body)

        # 2nd attempt: Success response with context manager
        mock_success = MagicMock()
        mock_success.read.return_value = json.dumps({
            "choices": [{"message": {"content": "Successfully recovered and synthesized report."}}]
        }).encode("utf-8")
        mock_success.__enter__.return_value = mock_success

        mock_urlopen.side_effect = [mock_err, mock_success]

        # Call with large prompt
        large_prompt = "Header\n" + ("x" * 6000) + "\nFooter"
        result = call_groq_api(
            system_prompt="System",
            user_prompt=large_prompt,
            api_key="mock_key",
            max_tokens=4000,
            max_retries=3,
        )

        self.assertEqual(result, "Successfully recovered and synthesized report.")
        self.assertEqual(mock_urlopen.call_count, 2)

    @patch("urllib.request.urlopen")
    def test_invalid_model_fallback(self, mock_urlopen):
        """Simulate an invalid model error that automatically falls back to active Groq model."""
        err_response_body = json.dumps({
            "error": {
                "message": "Model 'deprecated/old-model' not found.",
                "type": "invalid_request_error",
                "code": "model_not_found"
            }
        }).encode("utf-8")

        mock_err = urllib.error.HTTPError(
            url="https://api.groq.com/openai/v1/chat/completions",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=None,
        )
        mock_err.read = MagicMock(return_value=err_response_body)

        mock_success = MagicMock()
        mock_success.read.return_value = json.dumps({
            "choices": [{"message": {"content": "Fallback successful."}}]
        }).encode("utf-8")
        mock_success.__enter__.return_value = mock_success

        mock_urlopen.side_effect = [mock_err, mock_success]

        result = call_groq_api(
            system_prompt="System",
            user_prompt="Hello",
            api_key="mock_key",
            model_name="deprecated/old-model",
            max_retries=3,
        )

        self.assertEqual(result, "Fallback successful.")
        self.assertEqual(mock_urlopen.call_count, 2)

    @patch("urllib.request.urlopen")
    def test_rich_error_unwrapping_on_terminal_failure(self, mock_urlopen):
        """Verify that unrecoverable errors raise descriptive RuntimeError with Groq JSON details."""
        err_response_body = json.dumps({
            "error": {
                "message": "Invalid authentication token provided.",
                "type": "invalid_request_error",
                "code": "invalid_api_key"
            }
        }).encode("utf-8")

        mock_err = urllib.error.HTTPError(
            url="https://api.groq.com/openai/v1/chat/completions",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=None,
        )
        mock_err.read = MagicMock(return_value=err_response_body)
        mock_urlopen.side_effect = mock_err

        with self.assertRaises(RuntimeError) as ctx:
            call_groq_api(
                system_prompt="System",
                user_prompt="Hello",
                api_key="bad_key",
                max_retries=1,
            )

        self.assertIn("Groq API Error 401 [invalid_api_key]", str(ctx.exception))
        self.assertIn("Invalid authentication token", str(ctx.exception))

    @patch("urllib.request.urlopen")
    def test_editor_execute_llm_call_recovery(self, mock_urlopen):
        """Verify that execute_llm_call in editor.py also auto-recovers from 400 context overflow."""
        err_response_body = json.dumps({
            "error": {
                "message": "Maximum context length exceeded.",
                "type": "invalid_request_error",
                "code": "context_length_exceeded"
            }
        }).encode("utf-8")

        mock_err = urllib.error.HTTPError(
            url="https://api.groq.com/openai/v1/chat/completions",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=None,
        )
        mock_err.read = MagicMock(return_value=err_response_body)

        mock_success = MagicMock()
        mock_success.read.return_value = json.dumps({
            "choices": [{"message": {"content": "Editor recovered."}}]
        }).encode("utf-8")
        mock_success.__enter__.return_value = mock_success

        mock_urlopen.side_effect = [mock_err, mock_success]

        large_prompt = "Instruction:\n" + ("y" * 6000)
        result = execute_llm_call(
            system_prompt="System",
            user_prompt=large_prompt,
            api_key="mock_key",
            max_tokens=4000,
            max_retries=3,
        )

        self.assertEqual(result, "Editor recovered.")
        self.assertEqual(mock_urlopen.call_count, 2)


if __name__ == "__main__":
    unittest.main()
