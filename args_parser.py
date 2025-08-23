from urllib.parse import urlparse
from argparse import ArgumentParser, ArgumentTypeError


def check_count(value):
    """Checks for the non-negative integer. Raises ArgumentTypeError if not."""
    try:
        int_value = int(value)
    except ValueError as e:
        raise ArgumentTypeError(f'Argument "{value}" must be an integer.') from e
    if int_value < 1:
        raise ArgumentTypeError(f'Argument "{value}" must be greater than 0.')
    return int_value


def validate_hosts(hosts: list[str]) -> None:
    """Checks hosts for validity. Raises ArgumentTypeError if host is invalid."""
    for host in hosts:
        try:
            parsed_host = urlparse(host)
        except ValueError as e:
            raise ArgumentTypeError(f'Argument "{host}" must be a valid URL.') from e
        if parsed_host.scheme not in ['http', 'https'] or not parsed_host.netloc:
            raise ArgumentTypeError(f'Argument "{host}" must be a valid URL.')


def convert_hosts(hosts: str) -> list[str]:
    """Checks and converts hosts to the list.
    Raises ArgumentTypeError if hosts are invalid.
    """
    sites = list(map(str.strip, hosts.split(",")))
    validate_hosts(sites)
    return sites


def convert_input_file(path: str) -> list[str]:
    """Converts the input file to a list. Raises ArgumentTypeError if any host is invalid."""
    with open(path, "r", encoding = "utf-8") as file:
        hosts = [line.strip() for line in file.readlines() if line.strip()]
    validate_hosts(hosts)
    return hosts



class ArgsParser(ArgumentParser):
    """Custom ArgumentParser implementation for site_checker."""
    def __init__(self):
        super().__init__(
            prog = "sites_checker",
            description = "Checks sites functionality.",
        )
        self.add_argument(
            "-C", "--count",
            help = "Count of requests.",
            type = check_count,
            default = 1
        )
        input_group = self.add_mutually_exclusive_group(required=True)
        input_group.add_argument(
            "-H", "--hosts",
            help = "List of hosts, separated by comma.",
            type = convert_hosts
        )
        input_group.add_argument(
            "-F", "--file",
            help = "File with list of hosts, split into lines.",
            type = convert_input_file,
            dest = "hosts"
        )
        self.add_argument(
            "-O", "--output",
            help = "Output file to save the output. If not specified, the output is sent to the console.",
        )
