import time
import enum
from typing import NamedTuple

import asyncio
import aiohttp

from args_parser import ArgsParser


class ResultStatus(enum.Enum):
    OK = "ok"
    FAILED = "failed"
    ERROR = "error"


class FetchResult(NamedTuple):
    status: ResultStatus
    time: int | float | None


async def fetch_once(session: aiohttp.ClientSession, host: str) -> FetchResult:
    """Fetch one request to host. Returns the FetchResult with status and request's time"""
    try:
        start = time.perf_counter()
        async with session.get(host) as response:
            seconds = round(time.perf_counter() - start, 3)
            if response.ok:
                return FetchResult(ResultStatus.OK, seconds)
            return FetchResult(ResultStatus.FAILED, seconds)
    except aiohttp.ClientError:
        return FetchResult(ResultStatus.ERROR, None)


class SitesChecker:
    """Async class for checking hosts' availability"""
    def __init__(self, count: int = 1,
                 hosts: list[str] | None = None,
                 output_file: str | None = None) -> None:
        self.hosts = hosts
        self.output_file = output_file
        self.count = count
        self.results = []

    async def fetch_host(self, session: aiohttp.ClientSession, host: str) -> dict:
        """Fetch all requests to the host and return information dict."""
        tasks = [fetch_once(session, host) for _ in range(self.count)]
        results: list[FetchResult] = await asyncio.gather(*tasks)
        info: dict[str, int | float | str | None] = {
            "host": host,
            "success": 0,
            "failed": 0,
            "errors": 0,
            "min": float("inf"),
            "max": float("-inf"),
            "avg": 0
        }
        for result in results:
            if result.status == ResultStatus.ERROR:
                info["errors"] += 1
                continue
            info["min"] = min(info["min"], result.time)
            info["max"] = max(info["max"], result.time)
            info["avg"] = round(
                (info["success"] * info["avg"] + result.time) / (info["success"] + 1),
                3
            )
            if result.status == ResultStatus.OK:
                info["success"] += 1
            else:
                info["failed"] += 1
        if info["success"] == 0 and info["failed"] == 0:
            info["avg"] = info["min"] = info["max"] = None
        return info

    async def start(self) -> None:
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_host(session, host) for host in self.hosts]
            self.results = await asyncio.gather(*tasks)

    def print_table(self):
        """Prints the table of results. If there are no hosts, does nothing."""
        if not self.results:
            return
        max_lens: dict[str, int] = {key: len(key) + 2 for key in self.results[0]}
        for info_host in self.results:
            for key, value in info_host.items():
                if value is None:
                    value = ""
                max_lens[key] = max(len(str(value)) + 2, max_lens[key])
        # dicts are ordered from Python 3.7
        border = "+" + "+".join("-" * (value + 2) for key, value in max_lens.items()) + "+"
        header = "|" + "|".join(f" {key.title().center(value)} " for key, value in max_lens.items()) + "|"
        lines = [border, header, border]
        for info_host in self.results:
            line = "|"
            for key, value in info_host.items():
                if value is None:
                    value = ""
                line += f" {str(value).center(max_lens[key])} |"
            lines.extend([line, border])
        if self.output_file:
            with open(self.output_file, "w", encoding="utf-8") as file:
                print(*lines, sep="\n", file=file)
        else:
            print(*lines, sep="\n")


async def main() -> None:
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
