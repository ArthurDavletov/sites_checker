"""
File for checking the availability of multiple sites.

Run python ./bench.py -h for help.
"""
import time
import enum
from dataclasses import dataclass

import asyncio
import aiohttp

from args_parser import ArgsParser


class ResultStatus(enum.Enum):
    """
    Enum-class for request status.

    OK - request ended with 2xx code.
    Failed - request ended with 4xx or 5xx codes.
    Error - request ended with an error (e.g. connection error).
    """
    OK = "ok"
    FAILED = "failed"
    ERROR = "error"


@dataclass
class FetchResult:
    """
    Class for storing fetch results.

    time - time taken for the request in seconds. float('-inf') if request errored.
    """
    status: ResultStatus
    time: float


async def fetch_once(session: aiohttp.ClientSession, host: str) -> FetchResult:
    """
    Fetch one request to host. Returns the FetchResult with status and request's time

    :param session: Aiohttp session
    :param host: URL
    :return: FetchResult with status and request's time
    """
    try:
        start = time.perf_counter()
        async with session.get(host) as response:
            seconds = round(time.perf_counter() - start, 3)
            if response.ok:
                return FetchResult(ResultStatus.OK, seconds)
            return FetchResult(ResultStatus.FAILED, seconds)
    except aiohttp.ClientError:
        return FetchResult(ResultStatus.ERROR, float("-inf"))


@dataclass
class HostInfo:
    """
    Class for storing information about host availability.    

    :param host: Host URL
    :param success: Number of successful requests
    :param failed: Number of failed requests (4xx or 5xx)
    :param errors: Number of errors
    :param min: Minimum response time. float('inf') if only error requests were made
    :param max: Maximum response time. float('-inf') if only error requests were made
    :param avg: Average response time. None if only error requests were made
    """
    host: str
    success: int = 0
    failed: int = 0
    errors: int = 0
    min: float = float("inf")
    max: float = float("-inf")
    avg: float | None = None

    def items(self):
        """Returns the items of the host info."""
        for key, value in self.__dict__.items():
            yield key, value

    def __getitem__(self, item):
        """Get item by key."""
        return self.__dict__[item]

class SitesChecker:
    """
    Async class for checking hosts' availability
    """
    def __init__(self,
                 hosts: list[str],
                 count: int = 1,
                 output_file: str | None = None) -> None:
        """
        Initialize SitesChecker.

        :param count: Number of requests to send to each host. Default is 1.
        :param hosts: List of hosts to check. If None, no hosts will be checked.
        :param output_file: File to write the results to.
        If None, results will be printed to stdout.
        """
        self.hosts = hosts
        self.output_file = output_file
        self.count = count
        self.results: list[HostInfo] = []

    async def fetch_host(self, session: aiohttp.ClientSession, host: str) -> HostInfo:
        """
        Fetch all requests to the host and return information dict.

        :param session: Aiohttp session
        :param host: URL
        :return: Information dict with host status
        """
        tasks = [fetch_once(session, host) for _ in range(self.count)]
        results: list[FetchResult] = await asyncio.gather(*tasks)
        info = HostInfo(host = host)
        for result in results:
            if result.status == ResultStatus.ERROR:
                info.errors += 1
                continue
            info.min = min(info.min, result.time)
            info.max = max(info.max, result.time)
            if info.avg is None:
                info.avg = 0.0
            info.avg = round(
                (info.success * info.avg + result.time) / (info.success + 1),
                3
            )
            if result.status == ResultStatus.OK:
                info.success += 1
            else:
                info.failed += 1
        return info

    async def start(self) -> None:
        """Start the sites checker."""
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_host(session, host) for host in self.hosts]
            self.results = await asyncio.gather(*tasks)

    def print_table(self):
        """Prints the table of results. If there are no hosts, does nothing."""
        if not self.results:
            return
        keys = ("host", "success", "failed", "errors", "min", "max", "avg")
        max_lens = {key: len(key) + 2 for key in keys}
        for info_host in self.results:
            for key, value in info_host.items():
                if value is None:
                    value = ""
                max_lens[key] = max(len(str(value)) + 2, max_lens[key])
        # dicts are ordered from Python 3.7
        border = "+" + "+".join("-" * (value + 2) for key, value in max_lens.items()) + "+"
        header = "|" + "|".join(f" {key.title().center(value)} "
                                for key, value in max_lens.items()) + "|"
        lines = [border, header, border]
        for info_host in self.results:
            line = "|"
            for key, value in info_host.items():
                if value is None or value in (float("inf"), float("-inf")):
                    value = ""
                line += f" {str(value).center(max_lens[key])} |"
            lines.extend([line, border])
        if self.output_file:
            with open(self.output_file, "w", encoding="utf-8") as file:
                print(*lines, sep="\n", file=file)
        else:
            print(*lines, sep="\n")


async def main() -> None:
    """Main entry point."""
    parser = ArgsParser()
    args = parser.parse_args()
    sites_checker = SitesChecker(
        hosts = args.hosts,
        count = args.count,
        output_file = args.output
    )
    await sites_checker.start()
    sites_checker.print_table()


if __name__ == '__main__':
    asyncio.run(main())
