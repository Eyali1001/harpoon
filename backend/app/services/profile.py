import re
import httpx
from app.config import get_settings

settings = get_settings()


async def fetch_public_profile(address: str) -> dict | None:
    """
    Fetch public profile info from Polymarket Gamma API.

    Returns dict with: name, pseudonym, profileImage, bio, proxyWallet, profileUrl
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.gamma_api_url}/public-profile",
                params={"address": address.lower()},
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                # Build profile URL using name or pseudonym
                username = data.get("name") or data.get("pseudonym")
                profile_url = f"https://polymarket.com/@{username}" if username else None

                return {
                    "name": data.get("name"),
                    "pseudonym": data.get("pseudonym"),
                    "profile_image": data.get("profileImage"),
                    "bio": data.get("bio"),
                    "proxy_wallet": data.get("proxyWallet"),
                    "profile_url": profile_url,
                }
    except Exception:
        pass
    return None


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
