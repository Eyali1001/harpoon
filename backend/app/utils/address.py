import re
from urllib.parse import urlparse


def is_valid_address(address: str) -> bool:
    if not address:
        return False
    return bool(re.match(r"^0x[a-fA-F0-9]{40}$", address))


def parse_address_input(input_str: str) -> str:
    input_str = input_str.strip()

    if is_valid_address(input_str):
        return input_str

    if "polymarket.com" in input_str:
        parsed = urlparse(input_str)
        path_parts = parsed.path.strip("/").split("/")

        if len(path_parts) >= 2 and path_parts[0] == "profile":
            identifier = path_parts[1]

            if is_valid_address(identifier):
                return identifier

            return identifier

    if input_str.startswith("0x"):
        return input_str

    return input_str
