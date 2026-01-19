import re


async def resolve_profile_to_address(profile_input: str) -> str | None:
    """
    Resolve input to a wallet address.

    Accepts:
    - Wallet address (0x...)
    - Profile URL with address (https://polymarket.com/profile/0x...)

    Note: Username-based profile URLs (@username) are not supported as
    Polymarket's API requires authentication for user lookups.
    """
    profile_input = profile_input.strip()

    # Already a valid address
    if re.match(r"^0x[a-fA-F0-9]{40}$", profile_input):
        return profile_input.lower()

    # Extract address from URL if present
    if "polymarket.com" in profile_input:
        # Look for address in URL: /profile/0x... or /@0x...
        match = re.search(r"(?:profile/|@)(0x[a-fA-F0-9]{40})", profile_input, re.IGNORECASE)
        if match:
            return match.group(1).lower()

    # Check if the input itself looks like an address (case-insensitive)
    if profile_input.lower().startswith("0x") and len(profile_input) == 42:
        if re.match(r"^0x[a-fA-F0-9]{40}$", profile_input, re.IGNORECASE):
            return profile_input.lower()

    return None
