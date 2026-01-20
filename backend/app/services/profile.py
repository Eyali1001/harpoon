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


async def search_profile_by_username(username: str) -> str | None:
    """
    Search for a profile by username using Gamma public-search API.

    Returns the proxy wallet address if found.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.gamma_api_url}/public-search",
                params={
                    "q": username,
                    "search_profiles": "true",
                    "limit_per_type": 1
                },
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                profiles = data.get("profiles", [])
                if profiles:
                    wallet = profiles[0].get("proxyWallet")
                    if wallet:
                        return wallet.lower()
    except Exception:
        pass
    return None


async def resolve_profile_to_address(profile_input: str) -> str | None:
    """
    Resolve input to a wallet address.

    Accepts:
    - Wallet address (0x...)
    - Profile URL (https://polymarket.com/profile/0x... or https://polymarket.com/@username)
    - Username (e.g., "Svitovid")
    """
    profile_input = profile_input.strip()

    # Already a valid address
    if re.match(r"^0x[a-fA-F0-9]{40}$", profile_input):
        return profile_input.lower()

    # Extract address or username from URL if present
    if "polymarket.com" in profile_input:
        # Look for address in URL: /profile/0x...
        match = re.search(r"profile/(0x[a-fA-F0-9]{40})", profile_input, re.IGNORECASE)
        if match:
            return match.group(1).lower()

        # Look for username in URL: /@username
        match = re.search(r"@([a-zA-Z0-9_-]+)", profile_input)
        if match:
            username = match.group(1)
            # If it looks like an address, return it directly
            if re.match(r"^0x[a-fA-F0-9]{40}$", username, re.IGNORECASE):
                return username.lower()
            # Otherwise search for the username
            return await search_profile_by_username(username)

    # Check if the input itself looks like an address (case-insensitive)
    if profile_input.lower().startswith("0x") and len(profile_input) == 42:
        if re.match(r"^0x[a-fA-F0-9]{40}$", profile_input, re.IGNORECASE):
            return profile_input.lower()

    # Try treating it as a username
    if re.match(r"^[a-zA-Z0-9_-]+$", profile_input) and len(profile_input) >= 2:
        return await search_profile_by_username(profile_input)

    return None
