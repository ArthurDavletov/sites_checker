"""Tests of argument parser and bench.py."""
import asyncio
import io
import shutil
import tempfile
import unittest
import pathlib
from unittest.mock import patch, AsyncMock
from argparse import ArgumentTypeError

import aiohttp

from args_parser import ArgsParser, validate_hosts, check_count, convert_input_file
from bench import SitesChecker, main


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


class BenchTestCase(unittest.IsolatedAsyncioTestCase):
    """Tests for site_checker."""
    def setUp(self) -> None:
        """Set up test environment. Create necessary temporary files and directories."""
        self.temp_dir = pathlib.Path(tempfile.mkdtemp())
        self.output_file = self.temp_dir / "output.txt"

    def tearDown(self) -> None:
        """Tear down test environment. Remove temporary files and directories."""
        shutil.rmtree(self.temp_dir)

    @staticmethod
    def create_mock_get(status: int,
                        delay: int | float = 0,
                        raises: type[Exception] | None = None) -> AsyncMock:
        """
        Create a mock GET request.
        
        :param status: HTTP-status code
        :param delay: Delay of the request's processing (in seconds)
        :param raises: Exception to raise while requesting (if any)

        :return: Mocked ClientResponse
        """
        mock_response = AsyncMock(spec=aiohttp.ClientResponse)
        mock_response.status = status
        mock_response.ok = status < 400
        async def delay_and_raise():
            if delay > 0:
                await asyncio.sleep(delay)
            if raises is not None:
                raise raises
            return mock_response
        mock_acm = AsyncMock()
        mock_acm.__aenter__.side_effect = delay_and_raise
        return mock_acm

    @patch("aiohttp.ClientSession.get")
    async def test_just_works(self, mock_get):
        """Test successful GET request."""
        mock_get.return_value = self.__class__.create_mock_get(200)
        hosts = ["https://example.com"]
        sites_checker = SitesChecker(hosts = hosts, count = 1)
        await sites_checker.start()
        info = sites_checker.results[0]
        self.assertEqual(info["host"], hosts[0])
        self.assertEqual(info["success"], 1)
        self.assertEqual(info["errors"], 0)
        self.assertEqual(info["failed"], 0)

    @patch("aiohttp.ClientSession.get")
    async def test_server_error(self, mock_get):
        """Test server error responses."""
        for e in (aiohttp.ClientError, aiohttp.ServerTimeoutError, aiohttp.ServerDisconnectedError):
            mock_get.return_value = self.__class__.create_mock_get(500, raises = e)
            hosts = ["https://verybadserver.error"]
            sites_checker = SitesChecker(hosts = hosts, count = 1)
            await sites_checker.start()
            info = sites_checker.results[0]
            self.assertEqual(info["host"], hosts[0])
            self.assertEqual(info["success"], 0)
            self.assertEqual(info["errors"], 1)
            self.assertEqual(info["failed"], 0)

    @patch("aiohttp.ClientSession.get")
    async def test_server_failed(self, mock_get):
        """Test server failed responses (4xx or 5xx status codes)."""
        hosts = ["https://workingbadserver.fails"]
        for status in (404, 500, 502):
            mock_get.return_value = self.__class__.create_mock_get(status)
            sites_checker = SitesChecker(hosts = hosts, count = 3)
            await sites_checker.start()
            info = sites_checker.results[0]
            self.assertEqual(info["host"], hosts[0])
            self.assertEqual(info["success"], 0)
            self.assertEqual(info["errors"], 0)
            self.assertEqual(info["failed"], 3)

    @patch("aiohttp.ClientSession.get")
    @patch("sys.stdout", new_callable=io.StringIO)
    async def test_print(self, mock_stdout, mock_get):
        """Test printing the results table to the console."""
        mock_get.return_value = self.__class__.create_mock_get(200)
        hosts = ["https://example.com"]
        sites_checker = SitesChecker(hosts = hosts, count = 2)
        await sites_checker.start()
        sites_checker.print_table()
        output = mock_stdout.getvalue()
        self.assertIn(hosts[0], output)
        self.assertIn("2", output)
        self.assertIn("0", output)

    @patch("aiohttp.ClientSession.get")
    async def test_file_output(self, mock_get):
        """Test writing the results table to a file."""
        mock_get.return_value = self.__class__.create_mock_get(200)
        hosts = ["https://example.com"]
        sites_checker = SitesChecker(hosts = hosts, count = 2, output_file = str(self.output_file))
        await sites_checker.start()
        sites_checker.print_table()
        with open(self.output_file, encoding = "utf-8") as file:
            output = file.read()
        self.assertIn(hosts[0], output)
        self.assertIn("2", output)
        self.assertIn("0", output)

    @patch("aiohttp.ClientSession.get")
    @patch("sys.stdout", new_callable=io.StringIO)
    async def test_empty_results(self, mock_stdout, mock_get):
        """Test empty results handling."""
        # This is impossible situation, because there's check for the hosts in args_parser
        mock_get.return_value = self.__class__.create_mock_get(200)
        hosts = []
        sites_checker = SitesChecker(hosts = hosts, count = 1)
        await sites_checker.start()
        sites_checker.print_table()
        output = mock_stdout.getvalue().strip()
        self.assertEqual(output, "")

    @patch("aiohttp.ClientSession.get")
    @patch("sys.stdout", new_callable = io.StringIO)
    async def test_error_site(self, mock_stdout, mock_get):
        """Test printing error sites table."""
        mock_get.return_value = self.__class__.create_mock_get(200, raises = aiohttp.ClientError)
        hosts = ["https://bad_site.com"]
        sites_checker = SitesChecker(hosts = hosts, count = 1)
        await sites_checker.start()
        sites_checker.print_table()
        output = mock_stdout.getvalue().strip()
        self.assertNotIn("None", output)
        self.assertNotIn("inf", output)
        self.assertIn("1", output)
        self.assertIn("0", output)

    @patch("aiohttp.ClientSession.get")
    async def test_asyncio(self, mock_get):
        """Test for asynchronous behavior."""
        mock_get.return_value = self.__class__.create_mock_get(200, 1)
        hosts = [f"https://example_{i}.com/" for i in range(1, 10)]
        sites_checker = SitesChecker(hosts = hosts, count = 5)
        start = asyncio.get_event_loop().time()
        await sites_checker.start()
        all_time = asyncio.get_event_loop().time() - start
        # 10 sites with 1-second delays and 5 counts
        # if program isn't async, it'll be 50 seconds
        self.assertLess(all_time, 5)

    @patch("aiohttp.ClientSession.get")
    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("sys.argv", ["bench.py", "-H", "https://example.com"])
    async def test_working_from_console(self, mock_stdout, mock_get):
        """Test working from console."""
        mock_get.return_value = self.__class__.create_mock_get(200)
        await main()
        output = mock_stdout.getvalue().strip()
        self.assertIn("example.com", output)
        self.assertIn("1", output)
        self.assertIn("0", output)
