import httpx
import re
from app.config import get_settings

settings = get_settings()


async def resolve_profile_to_address(profile_input: str) -> str | None:
    """
    Resolve a Polymarket profile URL or username to a wallet address.

    Accepts:
    - Wallet address (0x...)
    - Profile URL (https://polymarket.com/@username or https://polymarket.com/profile/username)
    - Username (@username or just username)
    """
    profile_input = profile_input.strip()

    # Already a valid address
    if re.match(r"^0x[a-fA-F0-9]{40}$", profile_input):
        return profile_input.lower()

    # Extract username from URL or @mention
    username = None

    if "polymarket.com" in profile_input:
        # URL format: https://polymarket.com/@username or /profile/username
        match = re.search(r"polymarket\.com/(?:@|profile/)([^/?#]+)", profile_input)
        if match:
            username = match.group(1)
    elif profile_input.startswith("@"):
        username = profile_input[1:]
    else:
        # Assume it's a username
        username = profile_input

    if not username:
        return None

    # Fetch the profile page to extract the wallet address
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://polymarket.com/@{username}",
                follow_redirects=True,
                timeout=15.0,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; Harpoon/1.0)"
                }
            )

            if response.status_code != 200:
                return None

            html = response.text

            # Look for wallet address patterns in the HTML
            # The page typically contains the proxy wallet address
            address_patterns = [
                r'"proxyWallet"\s*:\s*"(0x[a-fA-F0-9]{40})"',
                r'"wallet"\s*:\s*"(0x[a-fA-F0-9]{40})"',
                r'"address"\s*:\s*"(0x[a-fA-F0-9]{40})"',
                r'0x[a-fA-F0-9]{40}',
            ]

            for pattern in address_patterns:
                match = re.search(pattern, html)
                if match:
                    # Get the address (could be group(1) or group(0))
                    addr = match.group(1) if match.lastindex else match.group(0)
                    return addr.lower()

    except Exception:
        pass

    return None
