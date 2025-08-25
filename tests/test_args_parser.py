"""Tests for ArgsParser."""
import unittest
import io
import shutil
import tempfile
import pathlib
from unittest.mock import patch

from argparse import ArgumentTypeError

from args_parser import ArgsParser, validate_hosts, check_count, convert_input_file


class ArgsParserTestCase(unittest.TestCase):
    """Tests for ArgsParser."""
    def setUp(self):
        """Set up test environment. Create necessary temporary files and directories."""
        self.parser = ArgsParser()
        self.temp_path = pathlib.Path(tempfile.mkdtemp())
        self.correct_hosts_file = pathlib.Path(self.temp_path / "hosts.txt")
        self.output_file = pathlib.Path(self.temp_path / "output.txt")
        self.correct_hosts = "https://yandex.ru,https://google.com,https://example.com/"
        self.correct_hosts_file.write_text(self.correct_hosts.replace(",", "\n"),
                                           encoding="utf-8")

    def tearDown(self):
        """Tear down test environment. Remove temporary files and directories."""
        shutil.rmtree(self.temp_path)

    def test_just_works(self):
        """Just works test."""
        self.parser.parse_args(["-H", self.correct_hosts])
        # no raises

    def test_not_specified_count(self):
        """Test when count isn't specified (default 1)."""
        namespace = self.parser.parse_args(["-H", self.correct_hosts])
        self.assertEqual(namespace.count, 1)

    def test_specified_count(self):
        """Test when count is specified."""
        namespace = self.parser.parse_args(["-H", self.correct_hosts, "-C", "52"])
        self.assertEqual(namespace.count, 52)

    def test_different_names_of_args(self):
        """Test different names of arguments:
        -H --hosts, -C --count, -F --file, -O --output
        """
        a = self.parser.parse_args(["-H", self.correct_hosts])
        b = self.parser.parse_args(["--hosts", self.correct_hosts])
        self.assertEqual(a.hosts, b.hosts)
        a = self.parser.parse_args(["-H", self.correct_hosts, "-C", "52"])
        b = self.parser.parse_args(["-H", self.correct_hosts, "--count", "52"])
        self.assertEqual(a.count, b.count)
        a = self.parser.parse_args(["-F", str(self.correct_hosts_file)])
        b = self.parser.parse_args(["--file", str(self.correct_hosts_file)])
        self.assertEqual(a.hosts, b.hosts)
        a = self.parser.parse_args(["-H", self.correct_hosts, "-O", str(self.output_file)])
        b = self.parser.parse_args(["-H", self.correct_hosts, "--output", str(self.output_file)])
        self.assertEqual(a.output, b.output)

    def test_incorrect_hosts(self):
        """Test with incorrect hosts."""
        incorrect_hosts = [
            "https://[][][][][]",
            "test",
            "2025",
            "https:/202520252025.com",
            "http",
            ""
        ]
        for host in incorrect_hosts:
            self.assertRaises(ArgumentTypeError, validate_hosts, [host])

    def test_incorrect_count(self):
        """Test with incorrect count values. (values must be positive integers)"""
        incorrect_count = ["0", "-1", "abc", "1.1", "0,0", "-1.1", "*", ""]
        for count in incorrect_count:
            self.assertRaises(ArgumentTypeError, check_count, count)

    @patch("sys.stderr", new_callable=io.StringIO)
    def test_two_inputs(self, _):
        """Test with two input sources. There's must be exception."""
        with self.assertRaises(SystemExit) as error:
            self.parser.parse_args(["-H", self.correct_hosts, "-F", str(self.correct_hosts_file)])
        self.assertEqual(error.exception.code, 2)

    def test_correct_file_convert(self):
        """Test with correct conversion from file to hosts."""
        # file and hosts are equal
        hosts = convert_input_file(str(self.correct_hosts_file))
        self.assertListEqual(hosts, self.correct_hosts.split(","))
