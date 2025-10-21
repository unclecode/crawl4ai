"""
Test module for the extract_response_content utility function.

This module tests the fallback logic for extracting content from LLM responses,
ensuring it properly handles different response formats and fallback scenarios.
"""

import unittest
from unittest.mock import Mock
from crawl4ai.extraction_strategy import extract_response_content


class TestExtractResponseContent(unittest.TestCase):
    """Test suite for extract_response_content function."""

    def test_extract_from_standard_content_field(self):
        """Test extraction when content is in the standard message.content field."""
        # Create a mock response with standard content
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = "Standard content here"

        # Extract content
        result = extract_response_content(response)

        # Assert result
        self.assertEqual(result, "Standard content here")

    def test_extract_from_reasoning_content_fallback(self):
        """Test extraction falls back to reasoning_content when content is None."""
        # Create a mock response with None content but reasoning_content
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = None
        response.choices[0].message.reasoning_content = "Reasoning content here"

        # Extract content
        result = extract_response_content(response)

        # Assert result
        self.assertEqual(result, "Reasoning content here")

    def test_extract_from_reasoning_content_when_content_empty_string(self):
        """Test extraction falls back to reasoning_content when content is empty string."""
        # Create a mock response with empty string content but reasoning_content
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = ""
        response.choices[0].message.reasoning_content = "Reasoning content here"

        # Extract content
        result = extract_response_content(response)

        # Assert result
        self.assertEqual(result, "Reasoning content here")

    def test_extract_from_provider_specific_fields_refusal(self):
        """Test extraction falls back to provider_specific_fields.refusal."""
        # Create a mock response with None content and reasoning_content, but refusal
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = None
        response.choices[0].message.reasoning_content = None
        response.choices[0].message.provider_specific_fields = {
            "refusal": "Refusal content here"
        }

        # Extract content
        result = extract_response_content(response)

        # Assert result
        self.assertEqual(result, "Refusal content here")

    def test_extract_from_provider_specific_fields_empty_reasoning(self):
        """Test extraction falls back to refusal when reasoning_content is empty."""
        # Create a mock response with empty reasoning_content but refusal
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = ""
        response.choices[0].message.reasoning_content = ""
        response.choices[0].message.provider_specific_fields = {
            "refusal": "Refusal content here"
        }

        # Extract content
        result = extract_response_content(response)

        # Assert result
        self.assertEqual(result, "Refusal content here")

    def test_extract_returns_none_when_all_fields_empty(self):
        """Test extraction returns None when all content fields are empty/None."""
        # Create a mock response with all empty fields
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = None
        response.choices[0].message.reasoning_content = None
        response.choices[0].message.provider_specific_fields = {}

        # Extract content
        result = extract_response_content(response)

        # Assert result
        self.assertIsNone(result)

    def test_extract_with_missing_reasoning_content_attribute(self):
        """Test extraction when reasoning_content attribute doesn't exist."""
        # Create a mock response without reasoning_content attribute
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = None

        # Use spec to prevent auto-creation of reasoning_content
        message_mock = Mock(spec=["content", "provider_specific_fields"])
        message_mock.content = None
        message_mock.provider_specific_fields = {
            "refusal": "Refusal content here"
        }
        response.choices[0].message = message_mock

        # Extract content
        result = extract_response_content(response)

        # Assert result
        self.assertEqual(result, "Refusal content here")

    def test_extract_with_missing_provider_specific_fields(self):
        """Test extraction when provider_specific_fields doesn't exist."""
        # Create a mock response without provider_specific_fields
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()

        # Use spec to prevent auto-creation of provider_specific_fields
        message_mock = Mock(spec=["content", "reasoning_content"])
        message_mock.content = None
        message_mock.reasoning_content = None
        response.choices[0].message = message_mock

        # Extract content
        result = extract_response_content(response)

        # Assert result
        self.assertIsNone(result)

    def test_extract_with_none_provider_specific_fields(self):
        """Test extraction when provider_specific_fields is None."""
        # Create a mock response with None provider_specific_fields
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = None
        response.choices[0].message.reasoning_content = None
        response.choices[0].message.provider_specific_fields = None

        # Extract content
        result = extract_response_content(response)

        # Assert result
        self.assertIsNone(result)

    def test_extract_priority_order(self):
        """Test that extraction follows the correct priority order."""
        # Create a mock response with all fields populated
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = "Primary content"
        response.choices[0].message.reasoning_content = "Reasoning content"
        response.choices[0].message.provider_specific_fields = {
            "refusal": "Refusal content"
        }

        # Extract content - should return primary content
        result = extract_response_content(response)

        # Assert result is the primary content
        self.assertEqual(result, "Primary content")

    def test_extract_with_whitespace_content(self):
        """Test extraction behavior with whitespace-only content."""
        # Create a mock response with whitespace content
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = "   "  # Only whitespace
        response.choices[0].message.reasoning_content = "Reasoning content"

        # Extract content - whitespace should be considered "truthy"
        result = extract_response_content(response)

        # Assert result is the whitespace content (not the reasoning content)
        self.assertEqual(result, "   ")

    def test_extract_with_zero_as_content(self):
        """Test extraction behavior when content is the number 0."""
        # Create a mock response with 0 as content
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = 0
        response.choices[0].message.reasoning_content = "Reasoning content"

        # Extract content - 0 should be considered "falsy" and fall back
        result = extract_response_content(response)

        # Assert result falls back to reasoning content
        self.assertEqual(result, "Reasoning content")

    def test_extract_with_false_as_content(self):
        """Test extraction behavior when content is False."""
        # Create a mock response with False as content
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = False
        response.choices[0].message.reasoning_content = "Reasoning content"

        # Extract content - False should be considered "falsy" and fall back
        result = extract_response_content(response)

        # Assert result falls back to reasoning content
        self.assertEqual(result, "Reasoning content")

    def test_extract_with_complex_provider_specific_fields(self):
        """Test extraction with complex nested provider_specific_fields structure."""
        # Create a mock response with complex provider_specific_fields
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = None
        response.choices[0].message.reasoning_content = None
        response.choices[0].message.provider_specific_fields = {
            "refusal": "Refusal message",
            "other_field": "Other value",
            "nested": {
                "inner": "Inner value"
            }
        }

        # Extract content
        result = extract_response_content(response)

        # Assert result
        self.assertEqual(result, "Refusal message")

    def test_extract_with_missing_refusal_key(self):
        """Test extraction when provider_specific_fields exists but no refusal key."""
        # Create a mock response with provider_specific_fields but no refusal key
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = None
        response.choices[0].message.reasoning_content = None
        response.choices[0].message.provider_specific_fields = {
            "other_field": "Other value",
            "error": "Error message"
        }

        # Extract content
        result = extract_response_content(response)

        # Assert result is None since no refusal key
        self.assertIsNone(result)

    def test_extract_with_getattr_safety(self):
        """Test that getattr safely handles missing attributes without raising AttributeError."""
        # Create a basic mock without some attributes
        response = Mock()
        response.choices = [Mock()]

        # Use spec to create a message with only content attribute
        message = Mock(spec=['content'])
        message.content = None
        response.choices[0].message = message

        # This should not raise an AttributeError
        result = extract_response_content(response)

        # Should return None gracefully
        self.assertIsNone(result)


class TestExtractResponseContentIntegration(unittest.TestCase):
    """Integration tests for extract_response_content with realistic response objects."""

    def test_openai_style_response(self):
        """Test with OpenAI-style response structure."""
        # Create a more realistic OpenAI-style response
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = "OpenAI response content"
        response.choices[0].message.role = "assistant"

        result = extract_response_content(response)
        self.assertEqual(result, "OpenAI response content")

    def test_anthropic_style_response_with_reasoning(self):
        """Test with Anthropic-style response that might have reasoning_content."""
        # Create a response with reasoning content
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = None
        response.choices[0].message.reasoning_content = "This is my reasoning process..."

        result = extract_response_content(response)
        self.assertEqual(result, "This is my reasoning process...")

    def test_provider_with_refusal_mechanism(self):
        """Test with a provider that uses refusal mechanisms."""
        # Create a response with refusal
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = None
        response.choices[0].message.reasoning_content = None
        response.choices[0].message.provider_specific_fields = {
            "refusal": "I cannot fulfill this request because..."
        }

        result = extract_response_content(response)
        self.assertEqual(result, "I cannot fulfill this request because...")


class TestExtractResponseContentRealWorldUsage(unittest.TestCase):
    """Test the function in scenarios that match real-world usage in extraction strategies."""

    def test_llm_extraction_strategy_integration(self):
        """Test that the function works correctly when called from LLMExtractionStrategy context."""

        # Mock a real LLM response scenario where content is in reasoning_content
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = None
        response.choices[0].message.reasoning_content = '{"blocks": [{"content": "extracted data"}]}'

        # Test extraction
        result = extract_response_content(response)
        self.assertEqual(result, '{"blocks": [{"content": "extracted data"}]}')

        # Verify it can be used for JSON parsing
        import json

        parsed = json.loads(result)
        self.assertEqual(parsed["blocks"][0]["content"], "extracted data")

    def test_json_schema_generation_integration(self):
        """Test that the function works correctly when called from schema generation context."""
        # Mock a schema generation response with refusal
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = ""
        response.choices[0].message.reasoning_content = None
        response.choices[0].message.provider_specific_fields = {
            "refusal": '{"error": "Cannot generate schema for this content"}'
        }

        # Test extraction
        result = extract_response_content(response)
        self.assertEqual(result, '{"error": "Cannot generate schema for this content"}')

        # Verify it can be used for JSON parsing
        import json

        parsed = json.loads(result)
        self.assertEqual(parsed["error"], "Cannot generate schema for this content")

    def test_regex_pattern_generation_integration(self):
        """Test that the function works correctly when called from regex pattern generation context."""
        # Mock a regex pattern generation response
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message = Mock()
        response.choices[0].message.content = '{"email_pattern": "\\\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\\\.[A-Z|a-z]{2,}\\\\b"}'

        # Test extraction
        result = extract_response_content(response)
        self.assertEqual(result, '{"email_pattern": "\\\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\\\.[A-Z|a-z]{2,}\\\\b"}')

        # Verify it can be used for JSON parsing
        import json

        parsed = json.loads(result)
        self.assertIn("email_pattern", parsed)


if __name__ == "__main__":
    unittest.main()
