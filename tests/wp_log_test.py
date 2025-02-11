import unittest
from io import StringIO
import sys
from wp_log import print_e, print_ie, print_d, print_ok, print_s, print_saved, print_ow, print_finished, input_cyan
from unittest.mock import patch

# Tests only for check print function still print the message
class TestWpLog(unittest.TestCase):
    def setUp(self):
        self.held, sys.stderr = sys.stderr, StringIO()
        self.held_out, sys.stdout = sys.stdout, StringIO()

    def tearDown(self):
        sys.stderr = self.held
        sys.stdout = self.held_out

    def test_print_e(self):
        print_e("Error message")
        self.assertIn("Error message", sys.stderr.getvalue())

    def test_print_ie(self):
        print_ie("Internal error message")
        self.assertIn("Internal error message", sys.stderr.getvalue())

    def test_print_d(self):
        print_d("Debug message")
        self.assertIn("Debug message", sys.stderr.getvalue())

    def test_print_ok(self):
        print_ok("OK message")
        self.assertIn("OK message", sys.stderr.getvalue())

    def test_print_s(self):
        print_s("Success message")
        self.assertIn("Success message", sys.stderr.getvalue())

    def test_print_saved(self):
        print_saved("Saved message")
        self.assertIn("Saved message", sys.stdout.getvalue())

    def test_print_ow(self):
        print_ow("Overwrite message")
        self.assertIn("Overwrite message", sys.stdout.getvalue())

    def test_print_finished(self):
        print_finished("Finished message")
        self.assertIn("Finished message", sys.stdout.getvalue())

    @patch('builtins.input', return_value='Y')
    def test_input_cyan(self, mock_input):
        response = input_cyan("Prompt message")
        self.assertEqual(response, 'Y')
