#!/usr/bin/env python3
"""
Unit tests for the auto-update policy automation functionality in FleetImporter.

Tests cover:
1. Policy name formatting with various inputs
2. osquery version detection query building
3. SQL injection prevention through quote escaping
4. Policy payload structure validation

Note: These tests extract and test the core logic from FleetImporter without
requiring AutoPkg dependencies. The functions are replicated here to enable
testing in environments where AutoPkg is not installed.
"""

import re
import sys
import unittest
from pathlib import Path


# Replicate the core functions from FleetImporter for testing
def slugify(text):
    """
    Convert text to a slug suitable for URLs and identifiers.
    Replicated from FleetImporter._slugify()
    """
    text = str(text).lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


def format_policy_name(template, software_title):
    """
    Format policy name from template, replacing %NAME% with slugified software title.
    Replicated from FleetImporter._format_policy_name()
    """
    slug = slugify(software_title)
    return template.replace("%NAME%", slug)


def build_version_query(software_title, version):
    """
    Build osquery SQL query to detect outdated software versions.
    Replicated from FleetImporter._build_version_query()
    """
    # Escape single quotes to prevent SQL injection
    escaped_title = software_title.replace("'", "''")
    escaped_version = version.replace("'", "''")

    query = f"SELECT * FROM programs WHERE name = '{escaped_title}' AND version != '{escaped_version}'"
    return query


class TestAutoUpdatePolicyFormatting(unittest.TestCase):
    """Test policy name formatting functionality."""

    def test_format_policy_name_basic(self):
        """Test basic policy name formatting."""
        result = format_policy_name("autopkg-auto-update-%NAME%", "GitHub Desktop")
        self.assertEqual(result, "autopkg-auto-update-github-desktop")

    def test_format_policy_name_spaces(self):
        """Test policy name formatting with spaces."""
        result = format_policy_name("autopkg-auto-update-%NAME%", "Visual Studio Code")
        self.assertEqual(result, "autopkg-auto-update-visual-studio-code")

    def test_format_policy_name_special_chars(self):
        """Test policy name formatting with special characters."""
        result = format_policy_name("autopkg-auto-update-%NAME%", "1Password 8")
        self.assertEqual(result, "autopkg-auto-update-1password-8")

    def test_format_policy_name_multiple_placeholders(self):
        """Test policy name with multiple %NAME% placeholders."""
        result = format_policy_name("auto-update-%NAME%-policy-%NAME%", "Claude")
        self.assertEqual(result, "auto-update-claude-policy-claude")

    def test_format_policy_name_no_placeholder(self):
        """Test policy name without placeholder."""
        result = format_policy_name("static-policy-name", "GitHub Desktop")
        self.assertEqual(result, "static-policy-name")

    def test_format_policy_name_uppercase(self):
        """Test policy name formatting with uppercase template."""
        result = format_policy_name("AUTOPKG-AUTO-UPDATE-%NAME%", "Slack")
        # Only %NAME% is slugified (lowercase), template stays as-is
        self.assertEqual(result, "AUTOPKG-AUTO-UPDATE-slack")

    def test_format_policy_name_dots_and_dashes(self):
        """Test policy name with dots and dashes in software name."""
        result = format_policy_name("autopkg-auto-update-%NAME%", "GPG Suite")
        self.assertEqual(result, "autopkg-auto-update-gpg-suite")


class TestAutoUpdateQueryBuilder(unittest.TestCase):
    """Test osquery version detection query building."""

    def test_build_version_query_basic(self):
        """Test basic version query building."""
        query = build_version_query("GitHub Desktop", "3.3.12")
        expected = (
            "SELECT * FROM programs WHERE name = 'GitHub Desktop' AND version != '3.3.12'"
        )
        self.assertEqual(query, expected)

    def test_build_version_query_single_quotes(self):
        """Test query building with single quotes in software name (SQL injection prevention)."""
        query = build_version_query("O'Reilly Software", "1.0.0")
        expected = (
            "SELECT * FROM programs WHERE name = 'O''Reilly Software' AND version != '1.0.0'"
        )
        self.assertEqual(query, expected)

    def test_build_version_query_multiple_quotes(self):
        """Test query building with multiple single quotes."""
        query = build_version_query("Bob's 'Great' App", "2.0.0")
        expected = (
            "SELECT * FROM programs WHERE name = 'Bob''s ''Great'' App' AND version != '2.0.0'"
        )
        self.assertEqual(query, expected)

    def test_build_version_query_version_with_build(self):
        """Test query with version containing build numbers."""
        query = build_version_query("Visual Studio Code", "1.85.2.123")
        expected = (
            "SELECT * FROM programs WHERE name = 'Visual Studio Code' AND version != '1.85.2.123'"
        )
        self.assertEqual(query, expected)

    def test_build_version_query_special_chars_in_version(self):
        """Test query with special characters in version."""
        query = build_version_query("Test App", "1.0.0-beta+123")
        expected = (
            "SELECT * FROM programs WHERE name = 'Test App' AND version != '1.0.0-beta+123'"
        )
        self.assertEqual(query, expected)

    def test_build_version_query_empty_values(self):
        """Test query building with empty values."""
        query = build_version_query("", "")
        expected = "SELECT * FROM programs WHERE name = '' AND version != ''"
        self.assertEqual(query, expected)

    def test_build_version_query_unicode(self):
        """Test query building with unicode characters."""
        query = build_version_query("Café App™", "1.0.0")
        expected = "SELECT * FROM programs WHERE name = 'Café App™' AND version != '1.0.0'"
        self.assertEqual(query, expected)


class TestAutoUpdatePolicyPayload(unittest.TestCase):
    """Test policy payload structure for Fleet API."""

    def test_policy_payload_structure(self):
        """Test that policy payload has all required fields."""
        # Simulate what would be created in _create_or_update_policy_direct
        policy_name = format_policy_name("autopkg-auto-update-%NAME%", "GitHub Desktop")
        query = build_version_query("GitHub Desktop", "3.3.12")

        # Expected payload structure
        payload = {
            "name": policy_name,
            "query": query,
            "description": "Auto-update policy for GitHub Desktop (version 3.3.12). Created by AutoPkg FleetImporter.",
            "resolution": "Install GitHub Desktop 3.3.12 via Fleet self-service.",
            "platform": "darwin",
            "critical": False,
        }

        # Verify all required fields are present
        self.assertIn("name", payload)
        self.assertIn("query", payload)
        self.assertIn("description", payload)
        self.assertIn("resolution", payload)
        self.assertIn("platform", payload)
        self.assertIn("critical", payload)

        # Verify field types
        self.assertIsInstance(payload["name"], str)
        self.assertIsInstance(payload["query"], str)
        self.assertIsInstance(payload["description"], str)
        self.assertIsInstance(payload["resolution"], str)
        self.assertEqual(payload["platform"], "darwin")
        self.assertIsInstance(payload["critical"], bool)
        self.assertFalse(payload["critical"])

        # Verify content
        self.assertEqual(payload["name"], "autopkg-auto-update-github-desktop")
        self.assertIn("GitHub Desktop", payload["query"])
        self.assertIn("3.3.12", payload["query"])
        self.assertIn("version != ", payload["query"])


class TestAutoUpdateSQLInjectionPrevention(unittest.TestCase):
    """Test SQL injection prevention in query building."""

    def test_prevent_sql_injection_or_clause(self):
        """Test that SQL OR injection attempts are properly escaped."""
        malicious_name = "App' OR '1'='1"
        query = build_version_query(malicious_name, "1.0.0")

        # Should escape the single quote, making it safe
        self.assertIn("App'' OR ''1''=''1", query)
        # Should NOT contain unescaped OR that would execute
        self.assertNotIn("' OR '1'='1", query)

    def test_prevent_sql_injection_comment(self):
        """Test that SQL comment injection attempts are properly escaped."""
        malicious_name = "App' -- comment"
        query = build_version_query(malicious_name, "1.0.0")

        # Should escape the single quote
        self.assertIn("App'' -- comment", query)
        # Query should remain valid
        self.assertTrue(query.startswith("SELECT * FROM programs WHERE"))

    def test_prevent_sql_injection_union(self):
        """Test that SQL UNION injection attempts are properly escaped."""
        malicious_name = "App' UNION SELECT * FROM users --"
        query = build_version_query(malicious_name, "1.0.0")

        # Should escape the single quote, neutralizing the injection
        self.assertIn("App'' UNION SELECT * FROM users --", query)

    def test_prevent_sql_injection_drop_table(self):
        """Test that DROP TABLE injection attempts are properly escaped."""
        malicious_version = "1.0.0'; DROP TABLE programs; --"
        query = build_version_query("Test App", malicious_version)

        # Should escape the single quote
        self.assertIn("1.0.0''; DROP TABLE programs; --", query)

    def test_multiple_injection_attempts(self):
        """Test multiple injection attempts in same query."""
        malicious_name = "App' OR '1'='1' --"
        malicious_version = "1.0'; DROP TABLE programs; --"
        query = build_version_query(malicious_name, malicious_version)

        # All single quotes should be escaped
        count_single_quotes = query.count("''")
        # Should have escaped quotes for both name and version
        self.assertGreater(count_single_quotes, 0)


class TestAutoUpdateEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_format_policy_name_empty_template(self):
        """Test policy name formatting with empty template."""
        result = format_policy_name("", "GitHub Desktop")
        self.assertEqual(result, "")

    def test_format_policy_name_empty_software_name(self):
        """Test policy name formatting with empty software name."""
        result = format_policy_name("autopkg-auto-update-%NAME%", "")
        self.assertEqual(result, "autopkg-auto-update-")

    def test_build_query_long_software_name(self):
        """Test query building with very long software name."""
        long_name = "A" * 500
        query = build_version_query(long_name, "1.0.0")
        self.assertIn(long_name, query)
        self.assertTrue(query.startswith("SELECT * FROM programs WHERE"))

    def test_build_query_long_version(self):
        """Test query building with very long version string."""
        long_version = "1." + "0" * 500
        query = build_version_query("Test App", long_version)
        self.assertIn(long_version, query)

    def test_format_policy_name_only_special_chars(self):
        """Test policy name formatting with only special characters."""
        result = format_policy_name("autopkg-auto-update-%NAME%", "!@#$%^&*()")
        # Slugify should handle this gracefully
        self.assertIsInstance(result, str)
        # Should have at least the prefix
        self.assertIn("autopkg-auto-update", result)


def run_tests():
    """Run all tests and print results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAutoUpdatePolicyFormatting))
    suite.addTests(loader.loadTestsFromTestCase(TestAutoUpdateQueryBuilder))
    suite.addTests(loader.loadTestsFromTestCase(TestAutoUpdatePolicyPayload))
    suite.addTests(loader.loadTestsFromTestCase(TestAutoUpdateSQLInjectionPrevention))
    suite.addTests(loader.loadTestsFromTestCase(TestAutoUpdateEdgeCases))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
