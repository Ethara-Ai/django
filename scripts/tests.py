#! /usr/bin/env python

"""
Tests for scripts utilities.

Run from within the scripts/ folder with:

$ python -m unittest tests.py

Or from the repo root with:

$ PYTHONPATH=scripts/ python -m unittest scripts/tests.py
"""

import unittest

from prepare_commit_msg import process_commit_message


class ProcessCommitMessageTests(unittest.TestCase):
    def test_non_stable_branch_no_prefix_added(self):
        pass

    def test_non_stable_branch_period_added(self):
        pass

    def test_non_stable_branch_with_period_unchanged(self):
        pass

    def test_empty_body_unchanged(self):
        pass

    def test_only_blank_lines_unchanged(self):
        pass

    def test_adds_stable_prefix(self):
        pass

    def test_does_not_double_add_prefix(self):
        pass

    def test_summary_leading_whitespace_no_double_space_before_prefix(self):
        pass

    def test_capitalizes_first_letter(self):
        pass

    def test_capitalizes_first_letter_after_existing_prefix(self):
        pass

    def test_adds_trailing_period(self):
        pass

    def test_does_not_double_add_trailing_period(self):
        pass

    def test_adds_backport_note(self):
        pass

    def test_does_not_double_add_backport_note(self):
        pass

    def test_backport_note_separated_by_blank_line(self):
        pass

    def test_git_comments_preserved_at_end(self):
        pass

    def test_prefix_and_period_and_backport_combined(self):
        pass

    def test_no_cherry_sha_no_backport_note(self):
        pass

    def test_leading_blank_lines_stripped(self):
        pass
